Write-Host "PowerShell $((Get-Host).Version.ToString())"

venv/Scripts/activate

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

    # Use reflection to set the "folder selection" option
    # $dialogType = $dialog.GetType()
    # $dialogType
    # $dialogType.InvokeMember('SetOptions', 'InvokeMethod, NonPublic, Instance', $null, $dialog, @(32)) # FOS_PICKFOLDERS flag

    $result = $dialog.ShowDialog()

    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        # The result will be a file path including the dummy filename, need to get the directory name
        return [System.IO.Path]::GetDirectoryName($dialog.FileName)
    } else {
        return $null
    }
}

# Example usage:
$TempFolder = ".\temp"
$lastMangaFolderPathFile = "$TempFolder\last_path.txt"

New-Item -Path $TempFolder -ItemType Directory -Force | Out-Null
$InputPath = Select-FolderDialog
$InputPath | Set-Content -Path $lastMangaFolderPathFile -Encoding UTF8 -Force

Write-Host "`nSelected folder: " -NoNewline
Write-Host "$InputPath" -ForegroundColor Green

python main.py --input $InputPath

# Show exit confirmation
Write-Host "`nPress Enter to exit" -ForegroundColor Cyan -NoNewLine
Read-Host