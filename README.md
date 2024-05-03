# Azure DevOps Build Status Updater Script

This PowerShell script automates the process of enabling the "Report Build Status" setting for all build definitions across all projects within a specified Azure DevOps organization.

## Features

- **Organization-Wide Updates**: Iterates through all projects within an Azure DevOps organization to update build definitions.
- **Configurable**: Prompts for Azure DevOps organization name and Personal Access Token (PAT) at runtime.
- **Enhanced Logging**: Outputs operation results to a log file, including success or failure outcomes, response codes, and messages for comprehensive tracking.
- **Debug Mode**: Includes an optional debug mode for detailed logging of the script's API interactions.
- **Error Handling**: Implements robust error handling to continue updates across projects even in the face of failures, ensuring comprehensive processing.
- **Success/Failure Tracking**: Monitors and logs the outcome of each operation, providing clear visibility into the script's execution results.

## Prerequisites

Before running this script, ensure you have the following:

- **Azure DevOps Organization**: Access to an Azure DevOps organization where you have permissions to update build definitions.
- **Personal Access Token (PAT)**: A PAT with at least the Build (Read & write) scope. Create a PAT in Azure DevOps that grants the necessary permissions for the script to make changes.

## Setup

1. **Download the Script**: Clone the repository locally or download the script to a directory of your choice.
2. **Prepare PowerShell**: Ensure your PowerShell environment can execute scripts. Run the following command in PowerShell as an Administrator:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

## Running the Script

1. **Open PowerShell**: Navigate to the directory containing the script.
2. **Execute the Script**: Run the script by entering:
   ```powershell
   .\powershell\Build_status.ps1

## Caution

- This script modifies build definitions across all projects in the specified Azure DevOps organization.
- **Secure Your PAT**: Ensure your Personal Access Token is kept secure. Follow best practices for handling and storing tokens.

## Troubleshooting

- **Script Execution Policy**: If you encounter errors related to script execution policies, ensure you've set the appropriate execution policy as described in the Setup section.
- **PAT Permissions**: Verify that your PAT has the correct permissions if you encounter authentication or authorization errors. This may require adjusting the scope of your token in Azure DevOps.

# Azure DevOps Pipeline Update Script
This Python script automates the process of updating Azure DevOps YAML pipelines to pull code from GitHub instead of Azure Repos. It scans all projects and repositories within a specified Azure DevOps organization, identifies repositories with YAML pipelines, updates the pipelines to reference GitHub, and creates a branch and pull request for the changes.

## Prerequisites
Before you begin, ensure you have Python installed on your machine. Python 3.6 or later is recommended. You will also need pip for installing Python packages.

## Installation
Clone the repository or download the script:
bash
Copy code
git clone https://yourrepository.com/path/to/script.git
cd path/to/script

## Install required Python packages:
Use pip to install the required Python packages listed in the requirements.txt file. If you don't have a requirements.txt, you can install the packages directly:
bash
Copy code
pip install requests pyyaml gitpython python-dotenv

## Setup

### Creating the Personal Access Token (PAT)
Log in to your Azure DevOps account.
Navigate to User Settings > Personal Access Tokens.
Create New Token with the following scopes:
Code: Read & write (allows the script to clone and push to repositories).
Project and Team: Read (necessary to list projects).
Work Items: Read (if you need to link work items to pull requests).
Record this token securely as it will not be shown again.

### Setting up the Environment File
Create a .env file in the root of your project directory with the following contents:

ORGANIZATION=your-organization
PAT=your-personal-access-token
GITHUB_CONNECTION_NAME=your-github-service-connection-name
Replace your-organization, your-personal-access-token, and your-github-service-connection-name with the actual values.

## Configuration
ORGANIZATION: Your Azure DevOps organization name.
PAT: The Personal Access Token you generated.
GITHUB_CONNECTION_NAME: The name of the service connection in Azure DevOps that connects to your GitHub repository.

## Running the Script
To run the script, ensure you are in the root directory where the script is located and execute:

python update_pipeline_script.py

This will start the process, and the script will log its operations to a file named update_pipeline_log_YYYY-MM-DD.log in the current directory. Check this file for any logs regarding the operations performed by the script, including errors and information on the repositories processed.

## Logging
The script logs detailed information about its execution, including any errors encountered, in a daily timestamped log file. This is useful for debugging and verifying what changes were made.

## Security Considerations
Ensure your .env file is not included in version control to protect your credentials.
Regularly rotate your Personal Access Token to enhance security.
By following these instructions, you should be able to successfully set up and run the script to automate updating Azure DevOps YAML pipelines to pull from GitHub repositories.