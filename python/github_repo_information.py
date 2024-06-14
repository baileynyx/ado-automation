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
import magic
from dotenv import load_dotenv

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
    # Fetch the repository items to scan for file extensions
    contents_url = f"{repo_url}/contents"
    response = requests.get(contents_url, headers=headers)
    
    if response.status_code == 200:
        items = response.json()
        for item in items:
            if item['type'] == 'dir':
                continue
            path = item['path']
            file_extension = os.path.splitext(path)[1].lower()
            mime_type = magic.from_buffer(requests.get(item['download_url']).content, mime=True)
            if mime_type.startswith('text/'):
                # Map file extensions to programming languages
                if file_extension == '.py':
                    languages.add('Python')
                elif file_extension == '.js':
                    languages.add('JavaScript')
                elif file_extension == '.html':
                    languages.add('HTML')
                elif file_extension == '.css':
                    languages.add('CSS')
                # Add more file extensions and corresponding languages as needed
    return languages

# Function to populate team and owner information from the existing xlsx file
def populate_team_owner_info(xlsx_path):
    df_existing = pd.read_excel(xlsx_path)
    for index, row in df_existing.iterrows():
        repo_name = row['Repository Name']
        team_owner_dict[repo_name] = {
            'team': row['Team Name'],
            'owner': row['Owner']
        }

# Check if team information should be populated
if CATEGORY_LABEL_TEAM:
    existing_xlsx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'github_repos.xlsx')
    if os.path.exists(existing_xlsx_path):
        populate_team_owner_info(existing_xlsx_path)

# Fetch all repositories with error handling
repos_response = requests.get(f'{base_url}/repos', headers=headers)

if repos_response.status_code == 200:
    repos = repos_response.json()
else:
    print(f"Failed to fetch repositories: {repos_response.status_code} {repos_response.text}")
    exit()

for repo in repos:
    repo_name = repo['name']
    # Fetch the last commit date for the repository
    commits_url = f"https://api.github.com/repos/{organization}/{repo_name}/commits"
    commits_response = requests.get(commits_url, headers=headers)
    if commits_response.status_code == 200:
        commits_data = commits_response.json()
        last_commit_date = commits_data[0]['commit']['committer']['date'] if commits_data else 'No commits'
    else:
        last_commit_date = 'Failed to fetch commits'
    
    # Fetch detailed information to get the size with error handling
    repo_detail_response = requests.get(f"https://api.github.com/repos/{organization}/{repo_name}", headers=headers)
    
    if repo_detail_response.status_code == 200:
        repo_detail = repo_detail_response.json()
        repo_data = [repo_name, repo_detail.get('size', 'Unknown'), last_commit_date]
        
        if CATEGORY_LABEL_LANGUAGE:
            languages = detect_languages(f"https://api.github.com/repos/{organization}/{repo_name}")
            repo_data.append(', '.join(languages))

        if CATEGORY_LABEL_TEAM and repo_name in team_owner_dict:
            team_owner_info = team_owner_dict[repo_name]
            repo_data.extend([team_owner_info['team'], team_owner_info['owner']])
        else:
            # Add placeholder team and owner information if not found
            repo_data.extend(['N/A', 'N/A'])
        
        repositories_data.append(repo_data)
    else:
        print(f"Failed to fetch details for repository {repo_name}: {repo_detail_response.status_code} {repo_detail_response.text}")

# Define columns based on the enabled categories
columns = ['Repository Name', 'Size in KB', 'Last Commit Date']
if CATEGORY_LABEL_LANGUAGE:
    columns.append('Languages')
if CATEGORY_LABEL_TEAM:
    columns.extend(['Team Name', 'Owner'])

# Convert the repositories data into a Pandas DataFrame
df_repos = pd.DataFrame(repositories_data, columns=columns)

# Ensure the output directory exists
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
os.makedirs(output_dir, exist_ok=True)

# Export the DataFrame to an Excel file in the output directory
output_path = os.path.join(output_dir, 'github_repos.xlsx')
df_repos.to_excel(output_path, index=False)
