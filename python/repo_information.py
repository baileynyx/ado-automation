# Ensure you have pandas installed: pip install pandas
# Ensure you have requests installed: pip install requests
# Esnure you have openpyxl installed: pip install openpyxl

# Required PAT Permissions:
# 1. Code (Read) - Allows the script to list and read details about repositories.
# 2. Project and Team (Read) - Allows the script to list projects within the organization.

# These permissions ensure the script can access project and repository information without the ability to modify them, adhering to a principle of least privilege.

import requests
import pandas as pd
import base64

# Your personal access token (PAT) and organization name
pat = 'your-pat-here'
organization = 'your-org-here'
api_version = '6.0'

# Base64 encode the PAT
encoded_pat = base64.b64encode(bytes(':' + pat, 'utf-8')).decode('utf-8')
headers = {'Authorization': f'Basic {encoded_pat}'}

base_url = f'https://dev.azure.com/{organization}'

repositories_data = []

# Fetch all projects with error handling
projects_response = requests.get(f'{base_url}/_apis/projects?api-version={api_version}', headers=headers)

if projects_response.status_code == 200:
    projects = projects_response.json().get('value', [])
else:
    print(f"Failed to fetch projects: {projects_response.status_code} {projects_response.text}")
    exit()

for project in projects:
    project_name = project['name']
    # Fetch all repositories in the current project with error handling
    repos_response = requests.get(f'{base_url}/{project_name}/_apis/git/repositories?api-version={api_version}', headers=headers)
    
    if repos_response.status_code == 200:
        repos = repos_response.json().get('value', [])
    else:
        print(f"Failed to fetch repositories for project {project_name}: {repos_response.status_code} {repos_response.text}")
        continue

    for repo in repos:
        # Fetch the last commit date for the repository
        commits_url = f"{base_url}/{project_name}/_apis/git/repositories/{repo['id']}/commits?api-version={api_version}&$top=1"
        commits_response = requests.get(commits_url, headers=headers)
        if commits_response.status_code == 200:
            commits_data = commits_response.json().get('value', [])
            last_commit_date = commits_data[0]['committer']['date'] if commits_data else 'No commits'
        else:
            last_commit_date = 'Failed to fetch commits'
        
        # For each repository, fetch detailed information to get the size with error handling
        repo_detail_response = requests.get(f"{base_url}/{project_name}/_apis/git/repositories/{repo['id']}?api-version={api_version}", headers=headers)
        
        if repo_detail_response.status_code == 200:
            repo_detail = repo_detail_response.json()
            repositories_data.append([project_name, repo['name'], repo_detail.get('size', 'Unknown'), last_commit_date])
        else:
            print(f"Failed to fetch details for repository {repo['name']}: {repo_detail_response.status_code} {repo_detail_response.text}")

# Convert the repositories data into a Pandas DataFrame
df_repos = pd.DataFrame(repositories_data, columns=['Project Name', 'Repository Name', 'Size in Bytes', 'Last Commit Date'])

# Export the DataFrame to an Excel file
df_repos.to_excel('azure_devops_repos.xlsx', index=False)
