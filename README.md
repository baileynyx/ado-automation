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

- This script modifies build definitions across all projects in the specified Azure DevOps organization. **Test the script in a non-production environment** before running it against your main organization.
- **Secure Your PAT**: Ensure your Personal Access Token is kept secure. Follow best practices for handling and storing tokens.

## Troubleshooting

- **Script Execution Policy**: If you encounter errors related to script execution policies, ensure you've set the appropriate execution policy as described in the Setup section.
- **PAT Permissions**: Verify that your PAT has the correct permissions if you encounter authentication or authorization errors. This may require adjusting the scope of your token in Azure DevOps.
