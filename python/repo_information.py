# Ensure you have pandas installed: pip install pandas
# Ensure you have requests installed: pip install requests
# Note: The 'Authorization' header uses basic auth with your PAT. Ensure it's kept secure and not exposed.

# Required PAT Permissions:
# 1. Code (Read) - Allows the script to list and read details about repositories.
# 2. Project and Team (Read) - Allows the script to list projects within the organization.

# These permissions ensure the script can access project and repository information without the ability to modify them, adhering to a principle of least privilege.

import requests
import pandas as pd

# Your personal access token (PAT) and organization name. Replace these placeholders with your actual access token and organization name.
pat = 'your_personal_access_token'
organization = 'your_organization_name'
api_version = '6.0'

# Base URL for Azure DevOps REST API
base_url = f'https://dev.azure.com/{organization}'

# Headers for authentication.
headers = {
    'Authorization': f'Basic {pat}'
}

# Prepare a list to collect repositories data
repositories_data = []

# Fetch all projects
projects_response = requests.get(f'{base_url}/_apis/projects?api-version={api_version}', headers=headers)
projects = projects_response.json()['value']

for project in projects:
    project_name = project['name']
    # Fetch all repositories in the current project
    repos_response = requests.get(f'{base_url}/{project_name}/_apis/git/repositories?api-version={api_version}', headers=headers)
    repos = repos_response.json()['value']
    for repo in repos:
        # For each repository, fetch detailed information to get the size
        repo_detail_response = requests.get(f"{base_url}/{project_name}/_apis/git/repositories/{repo['id']}?api-version={api_version}", headers=headers)
        repo_detail = repo_detail_response.json()
        # Append repository details to the list
        repositories_data.append([project_name, repo['name'], repo_detail.get('size', 'Unknown')])

# Convert the repositories data into a Pandas DataFrame
df_repos = pd.DataFrame(repositories_data, columns=['Project Name', 'Repository Name', 'Size in Bytes'])

# Export the DataFrame to an Excel file
df_repos.to_excel('azure_devops_repos.xlsx', index=False)