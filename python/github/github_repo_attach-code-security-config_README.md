# GitHub Repository Code Security Configuration Attachment Tool

This Python script, `github_repo_attach-code-security-config.py`, is designed to automate the process of attaching a specific GitHub Advanced Security (GHAS) code security configuration to multiple GitHub repositories. It reads the list of repositories from a CSV file and attaches the specified code security configuration to each repository in batches.

## Usage

Usage:
```shell
python github_repo_attach-code-security-config.py [-h] owner config_name csv_path
```

Attach a code security configuration to GitHub repositories specified in a CSV file.

positional arguments:
  - `owner` - GitHub name of the user or organization name that owns the GitHub repositories.
  - `config_name` - Name of the code security configuration to attach to the repos.
  - `csv_path` - Path to the CSV file that contains repository names in a column named `Repo`.

options:
  - `-h,` or `--help` - show this help message and exit

## Prerequisites

Before you start using this script, ensure you have the following installed:
- Python 3.x
- `pandas`
- `requests`
- `base64`
- `os`
- `mimetypes`
- `python-dotenv`

After cloning the repo, you can install the necessary
Python packages by running:

```sh
pip install -r requirements.txt
```

## Configuration (.env file)

Create a `.env` file in the root directory of the repos with the following content:

```sh
GITHUB_PAT=your_personal_access_token_here
BATCH_SIZE=1
```

### GITHUB_PAT
GitHub Personal Access Token (PAT).

Replace `your_personal_access_token_here` with your GitHub Personal Access Token.
You need a GitHub Personal Access Token with scopes: `repo, write:org`

### BATCH_SIZE
The number of repositories to process in a batch.

Defaults to 1 if not set.

### API_TIMEOUT_SECONDS
The number of seconds to wait for a response from the GitHub API.

Defaults to 60 seconds if not set.

## CSV file setup
Prepare a CSV file where each row represents a GitHub repo that to be targetted.

The CSV file must have the following columns:
- `Repo` - The repository name.

Any other columns will be ignored.

Example CSV file contents:
```csv
Repo
a-repository-name
another-repository-name
```
