
import argparse
import base64
import os
import pandas as pd
from dotenv import load_dotenv

def get_base64_encoded_pat():
    """ Get the Personal Access Token (PAT) from the GITHUB_PAT environment variable as base64 encoded."""
    # Get the Personal Access Token (PAT) from environment variables.
    pat = os.getenv('GITHUB_PAT')
    if not pat:
        raise ValueError("GITHUB_PAT environment variable is not set.")

    # Base64 encode the PAT
    base64_encoded_pat = base64.b64encode(bytes(f'{pat}', 'utf-8')).decode('utf-8')

    return base64_encoded_pat

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

def get_code_security_config_id(base64_encoded_pat, owner, config_name):
    """
    Retrieves the ID of a code security configuration based on the owner and the configuration name.

    Parameters:
    owner (str): The owner of the GitHub repository.
    config_name (str): The name of the code security configuration.

    Returns:
    int: The ID of the code security configuration or None if not found.
    """

    raise NotImplementedError("The get_code_security_config_id(..) function is not implemented yet.")

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

        repo_names = get_repo_names_from_csv(args.csv_path)

        configuration_id = get_code_security_config_id(base64_encoded_pat, args.owner, args.config_name)

        # TODO: Get repository_id of each repo.
        # TODO: Attach code security configuration to each repository.

        print("Processing completed successfully.")

    except Exception as e:
        print("Processing failed.")
        print(f"ERROR: {e}")
        exit(1)
