# GitHub Repository Add Topics Automation Script

The `github_repo_add_topics.py` Python script allows you to automate the process of adding topics to GitHub repositories by reading the repository details and topics to be added from a CSV file.

The script will add the specified topics to the repos if the topics do not already exist. It will not remove any existing topics.

## Prerequisites

Before you start using this script, ensure you have the following installed:
- Python 3.x
- `pandas`
- `requests`
- `base64`
- `os`
- `mimetypes`
- `python-dotenv`

You can install the necessary Python packages by running:

```sh
pip install pandas requests python-dotenv
```

## Configuration

- Personal Access Token (PAT): You need a GitHub Personal Access Token with repo scope. This allows the script to list and read details about repositories, as well as update topics. Follow GitHub's documentation to create a PAT.

- .env File: Create a .env file in the root directory of the script with the following content:

```sh
GITHUB_PAT=your_personal_access_token_here
```

Replace `your_personal_access_token_here` with your GitHub Personal Access Token.

## CSV file setup
Prepare a CSV file where each row represents a GitHub repo that to be targetted.

The CSV file must have the following columns:

Owner: The GitHub organization or user name.
Repo: The repository name.
Topics: The topics you want to add to the repository, separated by semicolons (;). Maybe blank if no topics are to be added for the repo on that row.

```csv
Owner,Repo,Topics
AnOrgName,a-repository-name,topic1;topic2;topic3
AnotherOrgName,another-repository-name-2,topicA;topicB
```

## Usage
Run the script by executing the following command in your terminal:

```shell
python github_repo_add_topics.py path_to_your_csv_file.csv
```

Replace `path_to_your_csv_file.csv` with the path to your CSV file.

If no CSV file path is specified, the script will prompt for the path.

The script will process each repository listed in the CSV file and update its topics accordingly.

The script will add the specified topics to the repos if the topics do not already exist. It will not remove any existing topics.
