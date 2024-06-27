import sys
import time
import pandas as pd
import requests
import os
import base64
from dotenv import load_dotenv

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
    :raises CSVFileError: If there are issues with the CSV file or path.
    """

    if csv_path is None or not csv_path.strip():
        raise CSVFileNoPathError(csv_path)
    else:
        csv_path = csv_path.strip()

    print(f"Reading CSV file: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
        required_columns = ['Repo', 'Owner', 'Topics']
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

def safe_put_request(url, json, headers):
    """Makes a PUT request and handles rate limiting by waiting until the limit is reset."""
    response = requests.put(url, json=json, headers=headers)
    if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and response.headers['X-RateLimit-Remaining'] == '0':
        reset_time = get_rate_limit_reset_time(response)
        wait_for_rate_limit_reset(reset_time)
        return safe_put_request(url, json, headers)  # Retry the request
    return response

def split_topics(topics_str):
    """
    Splits a semicolon-separated string of topics into a list of topics.

    :param topics_str: A string containing topics separated by semicolons, None, or NaN.
    :return: A list of topics.
    """
    if topics_str is None or pd.isna(topics_str) or topics_str == '':
        return []
    else:
        return topics_str.split(';')

class TopicError(Exception):
    """Base exception class for GitHub topic-related errors."""
    def __init__(self, action, owner, repo, status_code, message):
        self.action = action
        self.owner = owner
        self.repo = repo
        self.status_code = status_code
        self.message = message
        super().__init__(f"Failed to {action} topics for {owner}/{repo}: {status_code}, {message}")

class TopicFetchError(TopicError):
    """Exception raised when fetching topics from a GitHub repository fails."""
    def __init__(self, owner, repo, status_code, message):
        super().__init__("fetch", owner, repo, status_code, message)

class TopicUpdateError(TopicError):
    """Exception raised when updating topics for a GitHub repository fails."""
    def __init__(self, owner, repo, status_code, message):
        super().__init__("update", owner, repo, status_code, message)

def get_current_repo_topics(base64_encoded_pat, owner, repo):
    """
    Fetches the current topics of a given GitHub repository.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :return: The current list topics. May be an empty list.
    :raises TopicFetchError: If fetching topics fails.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/topics"
    request_headers = {
        'Authorization': f'Basic {base64_encoded_pat}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = safe_get_request(url, headers=request_headers)
    if response.status_code == 200:
        return response.json().get('names', [])
    else:
        raise TopicFetchError(owner, repo, response.status_code, response.text)

def update_repo_topics(base64_encoded_pat, owner, repo, topics):
    """
    Updates the topics of a given GitHub repository.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param topics: A list of topics to update the repository with.
    :raises TopicUpdateError: If updating topics fails.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/topics"
    payload = {"names": topics}
    request_headers = {
        'Authorization': f'Basic {base64_encoded_pat}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = safe_put_request(url, json=payload, headers=request_headers)
    if response.status_code != 200:
        raise TopicUpdateError(owner, repo, response.status_code, response.text)

def add_topics_to_repo(base64_encoded_pat, owner, repo, new_topics):
    """
    Adds topics to a given GitHub repository without removing existing topics.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param new_topics: A list of new topics to add to the repository.
    :raises TopicError: If adding topics fails.
    """

    if not new_topics:
        print(f"Repo: {owner}/{repo}, Skipping. No topics provided.")
        return

    # Fetch current topics
    current_topics = get_current_repo_topics(base64_encoded_pat, owner, repo)

    # Check if all new topics are already in current topics.
    if set(new_topics).issubset(set(current_topics)):
        print(f"Repo: {owner}/{repo}, Skipping. All provided topics already exist: {new_topics}")
        return

    # Merge new topics with current topics without duplicates.
    updated_topics = list(set(current_topics + new_topics))

    print(f"Repo: {owner}/{repo}, Adding topics: {new_topics}")

    # Update the repository's topics
    update_repo_topics(base64_encoded_pat, owner, repo, updated_topics)

def process_csv(base64_encoded_pat, csv_path):
    """
    Processes each row in the CSV file to add topics to repositories.
    :raises CSVFileError: If there are issues with the CSV file or path.
    :raises TopicError: If adding topics fails.
    """
    df = read_csv_file(csv_path)

    for index, row in df.iterrows():
        repo = row['Repo']
        owner = row['Owner']
        topics = split_topics(row['Topics'])
        add_topics_to_repo(base64_encoded_pat, owner, repo, topics)

if __name__ == "__main__":

    try:

        # Load environment variables from .env file.
        load_dotenv()

        # Get the Personal Access Token (PAT) from environment variables.
        pat = os.getenv('GITHUB_PAT')
        # Base64 encode the PAT
        base64_encoded_pat = base64.b64encode(bytes(f'{pat}', 'utf-8')).decode('utf-8')

        # Check if a CSV file path is passed as a command-line argument.
        if len(sys.argv) > 1:
            csv_path = sys.argv[1]
        else:
            csv_path = input("Enter the path to the CSV file: ")

        process_csv(base64_encoded_pat, csv_path)

        print("Processing completed successfully.")

    except Exception as e:
        print("Processing failed.")
        print(f"ERROR: {e}")
        exit(1)
