param(
    [Parameter(Mandatory = $true)] [string] $SubscriptionId,
    [Parameter(Mandatory = $true)] [string] $ResourceGroup,
    [Parameter(Mandatory = $true)] [string] $Location,
    [Parameter(Mandatory = $true)] [string] $StorageAccountName,
    [Parameter(Mandatory = $true)] [string] $BackendApiBaseUrl
)

$ErrorActionPreference = "Stop"

function Invoke-Az {
    param([string]$Command)
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI command failed: $Command"
    }
}

Write-Host "Selecting subscription..."
Invoke-Az "az account set --subscription $SubscriptionId"

Write-Host "Creating resource group if needed..."
Invoke-Az "az group create --name $ResourceGroup --location $Location --output none"

Write-Host "Creating storage account if needed..."
Invoke-Az "az storage account create --name $StorageAccountName --resource-group $ResourceGroup --location $Location --sku Standard_LRS --kind StorageV2 --output none"

Write-Host "Enabling static website hosting..."
Invoke-Az "az storage blob service-properties update --account-name $StorageAccountName --auth-mode login --static-website --index-document index.html --404-document index.html --output none"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$frontendPath = Join-Path $repoRoot "frontend"

Write-Host "Building frontend with production API URL..."
Push-Location $frontendPath
$env:VITE_API_BASE_URL = $BackendApiBaseUrl
npm ci
npm run build
Pop-Location

$distPath = Join-Path $frontendPath "dist"

Write-Host "Uploading dist/ to `$web container..."
$accountKey = az storage account keys list --account-name $StorageAccountName --resource-group $ResourceGroup --query "[0].value" -o tsv
if (-not $accountKey) {
    throw "Unable to fetch storage account key for $StorageAccountName"
}
Invoke-Az "az storage blob upload-batch --account-name $StorageAccountName --account-key $accountKey --destination `'$web`' --source `"$distPath`" --overwrite --output none"

$webUrl = az storage account show --name $StorageAccountName --resource-group $ResourceGroup --query "primaryEndpoints.web" -o tsv
Write-Host "Done. Frontend URL: $webUrl"
