
import argparse
import base64
import os
import pandas as pd
import requests
import time
from dotenv import load_dotenv
from math import ceil

class EnvVarMissingError(Exception):
    """Exception raised when an expected environment variable is missing."""
    def __init__(self, env_var_name):
        self.message = f"{env_var_name} environment variable is not set."
        super().__init__(self.message)

def get_environment_variable_or_raise(env_var_name):
    value = os.getenv(env_var_name)
    if not value:
        raise EnvVarMissingError(env_var_name)
    return value

def get_base64_encoded_pat():
    """ Get the Personal Access Token (PAT) from the GITHUB_PAT environment variable as base64 encoded."""
    pat = get_environment_variable_or_raise('GITHUB_PAT')
    base64_encoded_pat = base64.b64encode(bytes(f'{pat}', 'utf-8')).decode('utf-8')

    return base64_encoded_pat

def get_repo_batch_size():
    batch_size = os.getenv("BATCH_SIZE", 1)
    print(f"Batch Size: {batch_size}")
    return int(batch_size)

# Usage example
get_repo_batch_size()

class CSVFileError(Exception):
    """Base exception class for CSV file-related errors."""
    def __init__(self, csv_path, message):
        self.csv_path = csv_path
        super().__init__(f"{message} Path: '{csv_path}'")

class CSVFileNoPathError(CSVFileError):
    """Exception raised when the CSV file path is not provided."""
    def __init__(self, csv_path):
        message = "The CSV file path was not provided."
        super().__init__(csv_path, message)

class CSVFileNotFoundError(CSVFileError):
    """Exception raised when the CSV file is not found."""
    def __init__(self, csv_path):
        message = "The CSV file was not found."
        super().__init__(message)

class CSVFileEmptyError(CSVFileError):
    """Exception raised when the CSV file is empty."""
    def __init__(self, csv_path):
        message = "The CSV file is empty."
        super().__init__(message)

class CSVFileColumnsError(CSVFileError):
    """Exception raised when the CSV file does not contain the required columns."""
    def __init__(self, csv_path, required_columns):
        message = f"The CSV file must contain the following columns: {', '.join(required_columns)}"
        super().__init__(csv_path, message)

class CSVFileParseError(CSVFileError):
    """Exception raised when there is an error parsing the CSV file."""
    def __init__(self, csv_path):
        message = "Error parsing the CSV file."
        super().__init__(message)

def read_csv_file(csv_path):
    """
    Reads a CSV file and returns a DataFrame if it contains the required columns.
    :return: DataFrame containing the CSV data.
    :raises CSVFileError: If there are issues with the CSV file or path.
    """

    if csv_path is None or not csv_path.strip():
        raise CSVFileNoPathError(csv_path)
    else:
        csv_path = csv_path.strip()

    print(f"Reading CSV file: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
        required_columns = ['Repo']
        if not all(column in df.columns for column in required_columns):
            raise CSVFileColumnsError(csv_path, required_columns)
        return df
    except FileNotFoundError:
        raise CSVFileNotFoundError(csv_path)
    except pd.errors.EmptyDataError:
        raise CSVFileEmptyError(csv_path)
    except pd.errors.ParserError:
        raise CSVFileParseError(csv_path)
    except CSVFileColumnsError:
        raise
    except Exception as e:
        raise CSVFileError(csv_path, f"An unexpected error occurred reading CSV file. Exception: {e}")

def get_repo_names_from_csv(csv_path):

    df = read_csv_file(csv_path)

    repo_names = df['Repo'].tolist()

    print(f"Repo Names: {repo_names}")

    return repo_names

def get_rate_limit_reset_time(response):
    """ Extracts the rate limit reset time from the response headers. """
    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
    return reset_time

def wait_for_rate_limit_reset(reset_time):
    """ Waits until the rate limit reset time. """
    wait_time = reset_time - int(time.time()) + 10  # Adding a 10-second buffer.
    if wait_time > 0:
        print(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
        time.sleep(wait_time)

def safe_get_request(url, headers):
    """ Makes a request and handles rate limiting by waiting until the limit is reset."""
    response = requests.get(url, headers=headers)
    if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and response.headers['X-RateLimit-Remaining'] == '0':
        reset_time = get_rate_limit_reset_time(response)
        wait_for_rate_limit_reset(reset_time)
        return safe_get_request(url, headers)  # Retry the request
    return response

def safe_patch_request(url, headers, json):
    """Makes a PATCH request and handles rate limiting by waiting until the limit is reset."""
    response = requests.put(url, json=json, headers=headers)
    if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and response.headers['X-RateLimit-Remaining'] == '0':
        reset_time = get_rate_limit_reset_time(response)
        wait_for_rate_limit_reset(reset_time)
        return safe_patch_request(url, headers, json)  # Retry the request
    return response

class CodeSecurityConfigNotFoundError(Exception):
    """Exception raised when the code security configuration is not found."""
    def __init__(self, owner, config_name):
        message = f"Code security configuration '{config_name}' not found for owner '{owner}'."
        super().__init__(message)

class CodeSecurityConfigRetrievalError(Exception):
    """Exception raised when there is an error retrieving the code security configuration."""
    def __init__(self, error_message):
        message = f"Failed to retrieve code security configuration: {error_message}"
        super().__init__(message)

def get_code_security_config_id(base64_encoded_pat, owner, config_name):
    """
    Retrieves the ID of a specific code security configuration for a GitHub organization.

    :param base64_encoded_pat: The GitHub Personal Access Token (PAT) encoded in base64.
                               This is used for authentication with the GitHub API.
    :param owner: The name of the GitHub organization owning the repos and code security configurations.
    :param config_name: The name of the code security configuration to retrieve the ID for.
    :return: The ID of the code security configuration if found.
    :raises CodeSecurityConfigNotFoundError: If no configuration with the given name is found for the owner.
    :raises CodeSecurityConfigRetrievalError: If there is an error in retrieving the configurations from GitHub.
    """
    try:
        print(f"Retrieving code security configurations for owner: '{owner}'")

        url = f"https://api.github.com/orgs/{owner}/code-security/configurations"
        request_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Basic {base64_encoded_pat}",
        }

        response = safe_get_request(url, headers=request_headers)
        response.raise_for_status()  # Raises an HTTPError if the response status code is 4XX/5XX

        configs = response.json()

        for config in configs:
            if config['name'] == config_name:
                configuration_id = config['id']
                print(f"Configuration Name: {config_name} has ID: {configuration_id}")
                return config['id']

        # If the configuration name is not found, raise an exception
        raise CodeSecurityConfigNotFoundError(owner, config_name)

    except requests.exceptions.RequestException as e:
        # Raise a custom exception with the original error message
        raise CodeSecurityConfigRetrievalError(str(e))

def get_code_security_config(base64_encoded_pat, owner, configuration_id):
    """
    Retrieves a specific code security configuration by its ID for a GitHub organization.

    :param base64_encoded_pat: The GitHub Personal Access Token (PAT) encoded in base64.
                               This is used for authentication with the GitHub API.
    :param owner: The name of the GitHub organization owning the repos and code security configurations.
    :param configuration_id: The ID of the code security configuration to retrieve.
    :return: The code security configuration if found.
    :raises CodeSecurityConfigRetrievalError: If there is an error in retrieving the configuration from GitHub.
    """
    try:
        print(f"Retrieving code security configuration ID: '{configuration_id}' for owner: '{owner}'")
        url = f"https://api.github.com/orgs/{owner}/code-security/configurations/{configuration_id}"
        request_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Basic {base64_encoded_pat}",
        }
        response = safe_get_request(url, headers=request_headers)
        response.raise_for_status()  # Raises an HTTPError if the response status code is 4XX/5XX

        configJson = response.json()
        print(f"\nConfiguration JSON:\n{configJson}\n")
        return configJson
    except requests.exceptions.RequestException as e:
        raise CodeSecurityConfigRetrievalError(str(e))

class CodeSecurityConfigAttachReposError(Exception):
    """Exception raised when attaching a code security configuration to repositories fails."""
    def __init__(self, response, configuration_id, repo_ids_list):
        self.configuration_id = configuration_id
        self.repo_ids_list = repo_ids_list
        self.error_message = f"Failed to attach configuration {configuration_id} to repositories {repo_ids_list}: HTTP Status Code: {response.status_code}, {response.text}"
        super().__init__(self.error_message)

def attach_config_to_repos(base64_encoded_pat, owner, configuration_id, repo_ids_list):
    """
    Attaches a code security configuration to multiple GitHub repositories with a single API call.

    :param base64_encoded_pat: The Base64 encoded Personal Access Token for GitHub API authentication.
    :param owner: The GitHub username or organization name that owns the repositories.
    :param configuration_id: The ID of the code security configuration to attach.
    :param repo_ids_list: A list of repository IDs to which the configuration will be attached.
    :type repo_ids_list: list
    :raises CodeSecurityConfigAttachReposError: Raises an exception if the API call fails or returns an error.
    """
    api_url = f"https://api.github.com/orgs/{owner}/code-security/configurations/{configuration_id}/attach"
    request_headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Basic {base64_encoded_pat}"
    }

    data = {
        "scope": "selected",
        "selected_repository_ids": repo_ids_list
    }
    print(f"Attaching configuration {configuration_id} to repos. Data: {data}")

    response = safe_patch_request(api_url, headers=request_headers, json=data)
    response.raise_for_status()  # Raises an HTTPError if the response status code is 4XX/5XX

    # Check if the request was successful
    if response.status_code not in [202]:
        raise CodeSecurityConfigAttachReposError(response, configuration_id, repo_ids_list)

    print("Configuration attached successfully to all specified repositories.")

class RepositoryNotFoundError(Exception):
    """Exception raised when a GitHub repository is not found."""
    def __init__(self, repo_name, owner):
        self.repo_name = repo_name
        self.owner = owner
        self.message = f"Repository '{repo_name}' not found for owner '{owner}'."
        super().__init__(self.message)

def get_repo_ids_from_names(base64_encoded_pat, owner, repo_names):
    """
    Fetches the IDs of given GitHub repositories for a specific owner using a Base64 encoded Personal Access Token (PAT).

    This function sends a GET request to the GitHub API for each repository name provided in the `repo_names` list. It constructs a dictionary mapping each repository name to its corresponding ID as found in the GitHub API response. If a repository does not exist, a `RepositoryNotFoundError` is raised.

    :param base64_encoded_pat: The Base64 encoded Personal Access Token used for authentication with the GitHub API.
    :param owner: The owner of the repositories. This is typically a user or organization name.
    :param repo_names: A list of repository names for which IDs are to be fetched.
    :return: A dictionary mapping repository names to their respective IDs.
    :rtype: dict
    :raises RepositoryNotFoundError: If any of the repositories do not exist under the specified owner.
    """
    repo_ids = {}
    for repo_name in repo_names:
        repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        request_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Basic {base64_encoded_pat}",
        }
        response = requests.get(repo_url, headers=request_headers)
        if response.status_code == 200:
            repo_data = response.json()
            repo_ids[repo_name] = repo_data['id']
            print(f"Repository Name: {repo_name} has ID: {repo_data['id']}")
        else:
            raise RepositoryNotFoundError(repo_name, owner)
    return repo_ids

if __name__ == "__main__":

    try:
        # Load environment variables from .env file.
        load_dotenv()

        base64_encoded_pat = get_base64_encoded_pat()

        parser = argparse.ArgumentParser(description="Attach a code security configuration to GitHub repositories.")
        parser.add_argument("owner", help="GitHub name of the user or organization name that owns the GitHub repositories.")
        parser.add_argument("config_name", help="Name of the code security configuration to attach.")
        parser.add_argument("csv_path", help="Path to the CSV file containing repository names, in a column named `Repo`.")

        args = parser.parse_args()

        print(f"Owner: {args.owner}")
        print(f"Config Name: {args.config_name}")
        print(f"CSV Path: {args.csv_path}")

        configuration_id = get_code_security_config_id(base64_encoded_pat, args.owner, args.config_name)

        configuration = get_code_security_config(base64_encoded_pat, args.owner, configuration_id)

        repo_names = get_repo_names_from_csv(args.csv_path)

        batch_size = get_repo_batch_size()

        # Calculate the number of batches needed
        num_batches = ceil(len(repo_names) / batch_size)

        for i in range(num_batches):

            print(f"\nProcessing repo batch {i+1}/{num_batches}")

            # Calculate start and end index for the current batch
            start_idx = i * batch_size
            end_idx = start_idx + batch_size

            # Get the current batch of repository names
            batch_repo_names = repo_names[start_idx:end_idx]

            print(f"Number of repos in batch: {len(batch_repo_names)}")

            # Get repository IDs for the current batch
            batch_repos = get_repo_ids_from_names(base64_encoded_pat, args.owner, batch_repo_names)

            batch_repo_ids_list = list(batch_repos.values())
            print(f"Repository IDs: {batch_repo_ids_list}")

            attach_config_to_repos(base64_encoded_pat, args.owner, configuration_id, batch_repo_ids_list)

        print("Processing completed successfully.")

    except Exception as e:
        print("Processing failed.")
        print(f"ERROR: {type(e).__name__}: {e}")
        exit(1)
