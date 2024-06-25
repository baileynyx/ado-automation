# Ensure you have pandas installed: pip install pandas
# Ensure you have requests installed: pip install requests
# Ensure you have openpyxl installed: pip install openpyxl
# Ensure you have python-magic installed: pip install python-magic
# Ensure you have python-dotenv installed: pip install python-dotenv

# Required PAT Permissions:
# 1. repo (Read) - Allows the script to list and read details about repositories.

import requests
import pandas as pd
import base64
import os
import mimetypes
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Your personal access token (PAT) and organization name from environment variables
pat = os.getenv('GITHUB_PAT')
organization = os.getenv('GITHUB_ORG')

# Base64 encode the PAT
encoded_pat = base64.b64encode(bytes(f'{pat}', 'utf-8')).decode('utf-8')
headers = {'Authorization': f'Basic {encoded_pat}'}

base_url = f'https://api.github.com/orgs/{organization}'

repositories_data = []

# Environment variables for optional updates
CATEGORY_LABEL_TEAM = os.getenv('CATEGORY_LABEL_TEAM', 'false').lower() == 'true'
CATEGORY_LABEL_LANGUAGE = os.getenv('CATEGORY_LABEL_LANGUAGE', 'false').lower() == 'true'

# Dictionary to store team and owner information
team_owner_dict = {}

# Function to detect programming languages based on file extensions
def detect_languages(repo_url):
    languages = set()
    contents_url = f"{repo_url}/contents"
    response = safe_get_request(contents_url, headers=headers)

    if response.status_code == 200:
        items = response.json()
        for item in items:
            if item['type'] == 'dir':
                continue
            path = item['path']
            file_extension = os.path.splitext(path)[1].lower()
            mime_type, _ = mimetypes.guess_type(item['download_url'])
            if mime_type and mime_type.startswith('text/'):
                languages.add(file_extension)
    return languages

def populate_team_owner_info(xlsx_path):
    df_existing = pd.read_excel(xlsx_path)
    if 'Team Name' not in df_existing.columns or 'Owner' not in df_existing.columns:
        print("Skipping reading of previous team and owner data.")
        print(f"The 'Team Name' or 'Owner' columns were not found in: {xlsx_path}")
    else:
        print("Reading previous team and owner data.")
        for index, row in df_existing.iterrows():
            repo_name = row['Repository Name']
            team_owner_dict[repo_name] = {
                'team': row['Team Name'],
                'owner': row['Owner']
            }

# Extracts the rate limit reset time from the response headers.
def get_rate_limit_reset_time(response):
    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
    return reset_time

# Waits until the rate limit reset time.
def wait_for_rate_limit_reset(reset_time):
    wait_time = reset_time - int(time.time()) + 10  # Adding a 10-second buffer.
    if wait_time > 0:
        print(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
        time.sleep(wait_time)

# Makes a request and handles rate limiting by waiting until the limit is reset.
def safe_get_request(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and response.headers['X-RateLimit-Remaining'] == '0':
        reset_time = get_rate_limit_reset_time(response)
        wait_for_rate_limit_reset(reset_time)
        return safe_get_request(url, headers)  # Retry the request
    return response

def get_repository_data(organization, repo):
    repo_name = repo['name']
    print(f"Fetching details for repository {repo_name}")

    # Fetch commits to get the last commit date
    commits_url = f"https://api.github.com/repos/{organization}/{repo_name}/commits"
    commits_response = safe_get_request(commits_url, headers=headers)

    if commits_response.status_code == 200:
        commits_data = commits_response.json()
        last_commit_date = commits_data[0]['commit']['committer']['date'] if commits_data else 'No commits'
    else:
        last_commit_date = 'Failed to fetch commits'

    # Fetch detailed information to get the size with error handling
    repo_detail_response = safe_get_request(f"https://api.github.com/repos/{organization}/{repo_name}", headers=headers)

    if repo_detail_response.status_code == 200:
        repo_detail = repo_detail_response.json()
        repo_data = [repo_name, repo_detail.get('size', 'Unknown'), last_commit_date]

        if CATEGORY_LABEL_LANGUAGE:
            languages = detect_languages(f"https://api.github.com/repos/{organization}/{repo_name}")
            repo_data.append(', '.join(languages))

        if CATEGORY_LABEL_TEAM:
            if repo_name in team_owner_dict:
                team_owner_info = team_owner_dict[repo_name]
                repo_data.extend([team_owner_info['team'], team_owner_info['owner']])
            else:
                # Add placeholder team and owner information if not found
                repo_data.extend(['N/A', 'N/A'])

        return repo_data
    else:
        print(f"Failed to fetch details for repository {repo_name}: {repo_detail_response.status_code} {repo_detail_response.text}")
        return None

# Check if previous team and owner information should be reused.
if CATEGORY_LABEL_TEAM:
    existing_xlsx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'github_repos.xlsx')
    if os.path.exists(existing_xlsx_path):
        populate_team_owner_info(existing_xlsx_path)

# Fetch repositories with pagination
repos_url = f"{base_url}/repos"
page = 1
per_page = 3  # Max is 100.
num_repos = 0

while True:
    paginated_url = f"{repos_url}?per_page={per_page}&page={page}"
    response = safe_get_request(paginated_url, headers=headers)
    if response.status_code == 200:
        repos = response.json()
        if not repos:
            break  # Break the loop if no more repositories to fetch
        num_repos += len(repos)
        print(f"Page {page} with {len(repos)} repos. Total repos fetched: {num_repos}")
        for repo in repos:
            repo_data = get_repository_data(organization, repo)
            if repo_data:
                repositories_data.append(repo_data)
        page += 1  # Go to the next page
    else:
        print(f"Could not query repos from GitHub org {organization} on page {page}: {response.status_code}, {response.reason}")
        break

# Define columns based on the enabled categories
columns = ['Repository Name', 'Size in KB', 'Last Commit Date']
if CATEGORY_LABEL_LANGUAGE:
    columns.append('Languages')
if CATEGORY_LABEL_TEAM:
    columns.extend(['Team Name', 'Owner'])

# Convert the repositories data into a Pandas DataFrame
print("Preparing output data.")
df_repos = pd.DataFrame(repositories_data, columns=columns)

# Ensure the output directory exists
print("Preparing to output to Excel file.")
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
os.makedirs(output_dir, exist_ok=True)

# Export the DataFrame to an Excel file in the output directory
output_path = os.path.join(output_dir, 'github_repos.xlsx')
df_repos.to_excel(output_path, index=False)
print(f"Data exported to: {output_path}")
