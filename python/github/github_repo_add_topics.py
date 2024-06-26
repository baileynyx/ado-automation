import sys
import pandas as pd
import requests
import os
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Your personal access token (PAT) from environment variables
pat = os.getenv('GITHUB_PAT')

# Base64 encode the PAT
encoded_pat = base64.b64encode(bytes(f'{pat}', 'utf-8')).decode('utf-8')
headers = {
    'Authorization': f'Basic {encoded_pat}',
    'Accept': 'application/vnd.github.v3+json'
}

def read_csv_file(csv_path):
    """
    Reads a CSV file and returns a DataFrame if it contains the required columns.
    """

    print(f"Reading CSV file: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
        required_columns = ['Repo', 'Owner', 'Topics']
        if not all(column in df.columns for column in required_columns):
            print(f"ERROR: The CSV file must contain the following columns: {', '.join(required_columns)}")
            return None
        return df
    except FileNotFoundError:
        print("ERROR: The CSV file was not found.")
        return None
    except pd.errors.EmptyDataError:
        print("ERROR: The CSV file is empty.")
        return None
    except pd.errors.ParserError:
        print("ERROR: Error parsing the CSV file.")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred reading CSV file. Exception: {e}")
        return None

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


def add_topics_to_repo(owner, repo, topics):
    """
    Adds topics to a given GitHub repository.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param topics: A list of topics to add to the repository.
    :return: True if topics were successfully added, False otherwise.
    """

    print(f"Adding topics {topics} to repo: {owner}/{repo}")

    url = f"https://api.github.com/repos/{owner}/{repo}/topics"
    payload = {"names": topics}
    response = requests.put(url, json=payload, headers=headers)

    if response.status_code == 200:
        print(f"Successfully added topics to {repo}")
        return True
    else:
        print(f"ERROR: Failed to add topics to {repo}: {response.status_code}, {response.text}")
        return False

def process_csv(csv_path):
    """
    Processes each row in the CSV file to add topics to repositories.
    Returns True on success, False otherwise.
    """
    df = read_csv_file(csv_path)
    if df is None:
        return False

    try:
        for index, row in df.iterrows():
            repo = row['Repo']
            owner = row['Owner']
            # Assuming topics are separated by semicolon in the CSV
            topics = split_topics(row['Topics'])
            success = add_topics_to_repo(owner, repo, topics)
            if not success:
                return False
        return True
    except Exception as e:
        print(f"ERROR: An error occurred: {e}")
        return False

if __name__ == "__main__":

    # Check if a CSV file path is passed as a command-line argument
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = input("Enter the path to the CSV file: ")

    if not csv_path.strip():
        print("A path to a CSV file is required.")
        exit(1)

    success = process_csv(csv_path)
    if success:
        print("Processing completed successfully.")
    else:
        print("Processing failed.")
        exit(1)
