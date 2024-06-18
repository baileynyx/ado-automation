# Script initialization and parameters definition
param (
    [bool]$debug = $false  # Enables verbose logging if set to true, providing detailed operation insights.
)

# Defines the path for the log file where detailed execution logs will be saved.
$logFilePath = ".\logs\buildReportStatus.log"

# Prompts the user for essential inputs required for the script's operation.
$organization = Read-Host -Prompt "Enter your Azure DevOps organization name"  # Azure DevOps organization name.
$personalAccessToken = Read-Host -Prompt "Enter your Personal Access Token" -AsSecureString  # Personal Access Token for authentication.

# Converts the SecureString Personal Access Token to a plain text string for use in API authentication headers.
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($personalAccessToken)
$unsecurePersonalAccessToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Function to make calls to the Azure DevOps REST API.
function Invoke-AzureDevOpsAPI {
    param (
        [string]$Uri,  # The REST API endpoint URI.
        [string]$Method = 'Get',  # HTTP method for the API call.
        [string]$Body = $null,  # Request body for applicable HTTP methods.
        [string]$personalAccessToken,  # PAT for API authentication.
        [bool]$debug  # Debug flag to control verbose logging.
    )

    # Prepares the authentication header using the provided PAT.
    $base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$($personalAccessToken)"))
    $headers = @{
        Authorization = "Basic $base64AuthInfo"
        "Content-Type" = "application/json"
    }

    # Conditional logging based on the debug flag status.
    if ($debug) {
        Write-Output "[$(Get-Date -Format 'u')] Request URI: $Uri" | Out-File -Append -FilePath $logFilePath
        Write-Output "[$(Get-Date -Format 'u')] Request Method: $Method" | Out-File -Append -FilePath $logFilePath
        if ($Body -and $Method -notin @('Get', 'Delete')) {
            Write-Output "[$(Get-Date -Format 'u')] Request Body: $Body" | Out-File -Append -FilePath $logFilePath
        }
    }

    try {
        # Executes the API call and handles response logging based on debug mode.
        $response = if ($Method -in @('Post', 'Put', 'Patch')) {
            Invoke-RestMethod -Uri $Uri -Method $Method -Headers $headers -Body $Body
        } else {
            Invoke-RestMethod -Uri $Uri -Method $Method -Headers $headers
        }

        if ($debug) {
            Write-Output "[$(Get-Date -Format 'u')] Response: $($response | ConvertTo-Json -Depth 10)" | Out-File -Append -FilePath $logFilePath
        }
        return $response
    } catch {
        # Error handling and logging
        Write-Output "[$(Get-Date -Format 'u')] Error: $($_.Exception.Message)" | Out-File -Append -FilePath $logFilePath
        throw
    }
}

# Tracks the overall success of the script. It's set to false if any operation fails.
$scriptSuccess = $true

# Initiates an array to collect log entries for later output to the log file.
$logContent = @()

# Fetch all projects within the specified Azure DevOps organization.
$projectsUri = "https://dev.azure.com/$organization/_apis/projects?api-version=6.0"
$projects = Invoke-AzureDevOpsAPI -Uri $projectsUri -personalAccessToken $unsecurePersonalAccessToken -debug $debug

# Iterate through each project to process its build definitions.
foreach ($project in $projects.value) {
    $uriGet = "https://dev.azure.com/$organization/$($project.name)/_apis/build/definitions?api-version=6.0"
    $buildDefinitions = Invoke-AzureDevOpsAPI -Uri $uriGet -personalAccessToken $unsecurePersonalAccessToken -debug $debug

    if ($buildDefinitions.value.Count -eq 0) {
        # Logs a message if no build definitions are found in the current project.
        $logContent += "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`nOrganization: $organization`nProject: $($project.name)`nOutcome: No build definitions found.`n`n"
    } else {
        foreach ($def in $buildDefinitions.value) {
            # Constructs the URI for updating the specific build definition.
            $uri = "https://dev.azure.com/$organization/$($project.name)/_apis/build/definitions/$($def.id)?api-version=6.0"
            $currentDefinition = Invoke-AzureDevOpsAPI -Uri $uri -Method Get -personalAccessToken $unsecurePersonalAccessToken -debug $debug

            # Sets the "Report Build Status" property to true.
            $currentDefinition.repository.properties.reportBuildStatus = "true"
            $body = $currentDefinition | ConvertTo-Json -Depth 10 -Compress

            try {
                # Attempts to update the build definition with the new settings.
                $response = Invoke-AzureDevOpsAPI -Uri $uri -Method Put -Body $body -personalAccessToken $unsecurePersonalAccessToken -debug $debug
                $dateTimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                # Adds a success log entry for the current operation.
                $logContent += "Date: $dateTimeStamp`nOrganization: $organization`nProject: $($project.name)`nBuild Definition: $($def.name)`nOutcome: Success`n`n"
            } catch {
                $scriptSuccess = $false
                $errorMessage = $_.Exception.Message
                $responseCode = $_.Exception.Response.StatusCode.Value__
                $responseMessage = $_.Exception.Response.StatusDescription
                $dateTimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                $logContent += "Date: $dateTimeStamp`nOrganization: $organization`nProject: $($project.name)`nBuild Definition: $($def.name)`nOutcome: Failure`nResponse Code: $responseCode`nResponse Message: $responseMessage`nError Message: $errorMessage`n`n"
            }
        }
    }
}

# Output the accumulated log entries to the specified log file.
$logContent | Out-File -FilePath $logFilePath

# Check the overall success of the script and display an appropriate message.
if ($scriptSuccess) {
    Write-Host "All pipelines across all projects have been successfully updated."
} else {
    Write-Host "The script encountered errors during execution. Please check the log file at $logFilePath for details."
}
