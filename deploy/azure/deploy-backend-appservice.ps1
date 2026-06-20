param(
    [Parameter(Mandatory = $true)] [string] $SubscriptionId,
    [Parameter(Mandatory = $true)] [string] $ResourceGroup,
    [Parameter(Mandatory = $true)] [string] $Location,
    [Parameter(Mandatory = $true)] [string] $PlanName,
    [Parameter(Mandatory = $true)] [string] $WebAppName,
    [Parameter(Mandatory = $true)] [string] $DjangoSecretKey,
    [Parameter(Mandatory = $true)] [string] $FrontendOrigin,
    [string] $Sku = "B1",
    [string] $PythonRuntime = "PYTHON:3.12"
)

$ErrorActionPreference = "Stop"

function Invoke-Az {
    param([string]$Command)
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI command failed: $Command"
    }
}

$allowedHosts = "$WebAppName.azurewebsites.net"
$csrfTrusted = "https://$WebAppName.azurewebsites.net"

Write-Host "Selecting subscription..."
Invoke-Az "az account set --subscription $SubscriptionId"

Write-Host "Creating resource group if needed..."
Invoke-Az "az group create --name $ResourceGroup --location $Location --output none"

Write-Host "Creating Linux App Service plan if needed..."
Invoke-Az "az appservice plan create --name $PlanName --resource-group $ResourceGroup --location $Location --is-linux --sku $Sku --async-scaling-enabled true --output none"

Write-Host "Creating web app if needed..."
Invoke-Az "az webapp create --resource-group $ResourceGroup --plan $PlanName --name $WebAppName --runtime `"$PythonRuntime`" --output none"

Write-Host "Setting application settings..."
Invoke-Az "az webapp config appsettings set --resource-group $ResourceGroup --name $WebAppName --settings DJANGO_SECRET_KEY=\"$DjangoSecretKey\" DJANGO_DEBUG=\"False\" DJANGO_ALLOWED_HOSTS=\"$allowedHosts\" DJANGO_CSRF_TRUSTED_ORIGINS=\"$csrfTrusted\" CORS_ALLOWED_ORIGINS=\"$FrontendOrigin\" SCM_DO_BUILD_DURING_DEPLOYMENT=\"true\" --output none"

Write-Host "Setting startup command..."
Invoke-Az "az webapp config set --resource-group $ResourceGroup --name $WebAppName --startup-file `"bash startup.sh`" --output none"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backendPath = Join-Path $repoRoot "backend"
$zipPath = Join-Path $env:TEMP "ml360-backend-deploy.zip"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Write-Host "Creating deployment zip from backend/..."
Push-Location $backendPath
Compress-Archive -Path * -DestinationPath $zipPath
Pop-Location

Write-Host "Deploying zip package..."
Invoke-Az "az webapp deploy --resource-group $ResourceGroup --name $WebAppName --src-path `"$zipPath`" --type zip --output none"

Write-Host "Restarting web app..."
Invoke-Az "az webapp restart --resource-group $ResourceGroup --name $WebAppName --output none"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Write-Host "Done. Backend URL: https://$WebAppName.azurewebsites.net/api/health/"
