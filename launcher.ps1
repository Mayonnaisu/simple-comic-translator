# Change global preference for all errors to terminate the process
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $True

# Define function to select folder with OpenFileDialog
function Select-FolderDialog {
    # Load the assembly
    Add-Type -AssemblyName System.Windows.Forms

    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = "Select a Folder"
    # Set properties to make it work as a folder picker
    $dialog.Filter = "Folders|*.folder" # A dummy filter is required
    $dialog.CheckFileExists = $false
    $dialog.FileName = "Select Folder"

     # Set initial directory
    if (Test-Path -Path $lastMangaFolderPathFile) {
        $InitialDirectory = Get-Content -Path $lastMangaFolderPathFile -Encoding UTF8
    } else {
        $InitialDirectory = "$env:USERPROFILE"
    }
    $dialog.InitialDirectory = $InitialDirectory

    $result = $dialog.ShowDialog()

    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        # The result will be a file path including the dummy filename, need to get the directory name
        return [System.IO.Path]::GetDirectoryName($dialog.FileName)
    } else {
        Throw "Folder Selection Cancelled."
    }
}

# Define temp folder & last_path.txt path
$TempFolder = ".\temp"
$lastMangaFolderPathFile = "$TempFolder\last_path.txt"

# Start the launcher
try {
    # Display PowerShell version
    Write-Host "PowerShell $((Get-Host).Version.ToString())"

    # Create temp folder
    New-Item -Path $TempFolder -ItemType Directory -Force | Out-Null

    # Call the function for selecting folder
    $InputPath = Select-FolderDialog

    $InputPath | Set-Content -Path $lastMangaFolderPathFile -Encoding UTF8 -Force

    Write-Host "`nSelected folder: " -NoNewline
    Write-Host "$InputPath" -ForegroundColor Green

    # Activate Python virtual environment
    try {
        Write-Host "`nActivating Virtual Environment..." -ForegroundColor Yellow

        venv/Scripts/activate

        Write-Host "`nVirtual Environment Activated." -ForegroundColor Green
    } catch {
        Throw "`nERROR: Failed to Activate Virtual Environment!`n$($_.Exception.Message)"
    }

    # Run Simple Comic Translator
    try {
        Write-Host "`nRunning Simple Comic Translator... " -ForegroundColor Yellow

        python main.py --input $InputPath

        if ($LASTEXITCODE -ne 0) {
            Throw "Simple Comic Translator Ran into Exception!`nEXIT CODE: $LASTEXITCODE."
        } else {
            Write-Host "`nLauncher Ran Successfully." -ForegroundColor Green
        }
    } catch {
        Throw "`nERROR: $($_.Exception.Message)"
    }
} catch {
    Write-Host "`n$($_.Exception.Message)`n`nLauncher Ran into Error!" -ForegroundColor Red
}

# Show exit confirmation
Write-Host "`nPress Enter to exit" -ForegroundColor Cyan -NoNewLine
Read-Host