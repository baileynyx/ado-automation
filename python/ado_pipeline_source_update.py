import requests
import yaml
import base64
from datetime import datetime
from git import Repo
import os
import tempfile
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ORGANIZATION = os.getenv('ORGANIZATION')
PAT = os.getenv('PAT')
GITHUB_CONNECTION_NAME = os.getenv('GITHUB_CONNECTION_NAME')
API_URL = f"https://dev.azure.com/{ORGANIZATION}/"
AUTH_HEADERS = {
    'Authorization': f'Basic {base64.b64encode((":" + PAT).encode()).decode()}',
    'Content-Type': 'application/json'
}

# Setup Logging
log_filename = datetime.now().strftime('update_pipeline_log_%Y-%m-%d.log')
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_projects():
    url = f"{API_URL}_apis/projects?api-version=6.0"
    try:
        response = requests.get(url, headers=AUTH_HEADERS)
        response.raise_for_status()
        return response.json()['value']
    except requests.RequestException as e:
        logging.error(f"Failed to get projects: {str(e)}")
        return []

def get_repositories(project_id):
    url = f"{API_URL}_apis/git/repositories?project={project_id}&api-version=6.0"
    try:
        response = requests.get(url, headers=AUTH_HEADERS)
        response.raise_for_status()
        return response.json()['value']
    except requests.RequestException as e:
        logging.error(f"Failed to get repositories for project {project_id}: {str(e)}")
        return []

def get_yaml_files(repo, project_id):
    url = f"{API_URL}{project_id}/_apis/git/repositories/{repo['id']}/items?scopePath=/&recursionLevel=Full&api-version=6.0"
    try:
        response = requests.get(url, headers=AUTH_HEADERS)
        response.raise_for_status()
        return [item for item in response.json()['value'] if item['path'].endswith('.yml')]
    except requests.RequestException as e:
        logging.error(f"Failed to get YAML files for repository {repo['id']}: {str(e)}")
        return []

def clone_repo(repo):
    temp_dir = tempfile.mkdtemp()
    try:
        return Repo.clone_from(repo['webUrl'], temp_dir, depth=1, env={"GIT_ASKPASS": "echo", "GIT_USERNAME": "", "GIT_PASSWORD": PAT})
    except Exception as e:
        logging.error(f"Failed to clone repository {repo['name']}: {str(e)}")
        return None

def update_yaml_content(yaml_path, repo_name):
    try:
        with open(yaml_path) as file:
            yaml_data = yaml.safe_load(file)
        
        for repo in yaml_data.get('resources', {}).get('repositories', []):
            if repo.get('type', '') == 'git':
                repo['type'] = 'github'
                repo['name'] = repo_name
                repo['endpoint'] = GITHUB_CONNECTION_NAME

        with open(yaml_path, 'w') as file:
            yaml.safe_dump(yaml_data, file)
    except Exception as e:
        logging.error(f"Failed to update YAML file {yaml_path}: {str(e)}")

def push_changes(repo, branch_name):
    try:
        repo.git.checkout('HEAD', b=branch_name)
        repo.git.add(all=True)
        repo.git.commit('-m', 'Updated pipeline to pull from GitHub')
        repo.git.push('--set-upstream', 'origin', branch_name)
    except Exception as e:
        logging.error(f"Failed to push changes for {branch_name}: {str(e)}")

def create_pull_request(project_id, repo_id, branch_name, repo_name):
    url = f"{API_URL}{project_id}/_apis/git/repositories/{repo_id}/pullrequests?api-version=6.0"
    payload = {
        "sourceRefName": f"refs/heads/{branch_name}",
        "targetRefName": "refs/heads/master",
        "title": "Update source repository to GitHub",
        "description": "Automated pull request to update the pipeline source.",
        "reviewers": []
    }
    try:
        response = requests.post(url, headers=AUTH_HEADERS, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to create pull request in repository {repo_name}: {str(e)}")

def process_organization():
    projects = get_projects()
    for project in projects:
        project_id = project['id']
        project_name = project['name']
        repos = get_repositories(project_id)
        for repo in repos:
            repo_name = repo['name']
            yaml_files = get_yaml_files(repo, project_id)
            if yaml_files:
                local_repo = clone_repo(repo)
                if local_repo:
                    branch_name = f"{project_name}-source-fix"
                    for yaml_file in yaml_files:
                        update_yaml_content(os.path.join(local_repo.working_tree_dir, yaml_file['path']), repo_name)
                    push_changes(local_repo, branch_name)
                    create_pull_request(project_id, repo['id'], branch_name, repo_name)
                    logging.info(f"Updated: Project {project_name}, Repository {repo_name}, Branch {branch_name}")
            else:
                logging.info(f"No YAML Pipelines Found: Project {project_name}, Repository {repo_name}")

if __name__ == "__main__":
    process_organization()
