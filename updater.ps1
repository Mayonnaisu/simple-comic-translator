# Change global preference for all errors to terminate the process
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $True

# Suppress the default progress bar because it slows down process in stock PowerShell (5.1). See https://github.com/PowerShell/PowerShell/issues/2138.
$ProgressPreference = 'SilentlyContinue'

# Define update url & path
$repoUrl = "https://github.com/Mayonnaisu/simple-comic-translator/archive/refs/heads/main.zip"
$downloadPath = ".\temp\repo.zip"

try {
    # Unblock module
    Unblock-File -Path ".\app\extra\downloader.psm1"

    # Import module
    Import-Module ".\app\extra\downloader.psm1"

    # Display PowerShell version
    Write-Host "PowerShell $((Get-Host).Version.ToString())"

    # Download the latest .zip file from my repo
    Write-Host "`nDownloading Update from $repoUrl..." -ForegroundColor Yellow

    if (-not (Test-Path -Path ".\temp" -PathType Container)) {
        New-Item -Path ".\temp" -ItemType Directory -Force | Out-Null
    }

    Start-ResumableBitsDownload -JobName "Mayonnaisu-SCT" -SourceUrl $repoUrl -DestinationPath $downloadPath

    Write-Host "`nUpdate Downloaded to $downloadPath." -ForegroundColor Green

    try {
        # Extract repo.zip
        Write-Host "`nExtracting Update Contents..." -ForegroundColor Yellow

        $extractPath = ".\temp\repo"

        Expand-ArchiveWithProgress -ArchivePath $downloadPath -DestinationPath $extractPath

        Write-Host "`nUpdate Contents Extracted to $extractPath." -ForegroundColor Green

        # Delete the excluded files from the extracted content
        Write-Host "`nExcluding Files from Update...`n" -ForegroundColor Yellow

        $extractedContentPath = Get-ChildItem -Path $extractPath

        $filesToExclude = @(
            "config.json",
            "prompt.yaml",
            "filters/manga.txt",
            "filters/manhwa.txt",
            "filters/manhua.txt"
        )

        foreach ($item in $filesToExclude) {
            $itemPath = Join-Path -Path $extractedContentPath.FullName -ChildPath $item

            if (Test-Path $item) {
                if (Test-Path $itemPath) {
                    Write-Host "Excluding '$item'..." -ForegroundColor DarkYellow

                    Remove-Item -Path $itemPath -Recurse -Force

                    Write-Host "'$item' Excluded.`n" -ForegroundColor DarkGreen
                }
            }
        }

        Write-Host "Files Excluded from Update." -ForegroundColor Green

        # Copy the extracted content to current direcory
        $destinationPath = ".\"

        Copy-Item -Path "$($extractedContentPath.FullName)\*" -Destination $destinationPath -Recurse -Force

        Remove-Item -Path $extractPath -Recurse -Force -Confirm:$false

        # Activate Python venv
        try {
            Write-Host "`nActivating Virtual Environment..." -ForegroundColor Yellow

            venv\Scripts\activate

            Write-Host "`nVirtual Environment Activated." -ForegroundColor Green
        } catch {
            Throw "`nFailed to Activate Virtual Environment!`nERROR: $($_.Exception.Message)"
        }

        # Install new dependencies
        $requirementsPath = ".\requirements-lock.txt"

        Write-Host "`nInstalling New Dependencies..." -ForegroundColor Yellow

        if (-not (Test-Path -Path $requirementsPath)) {
            Throw "Path '$requirementsPath' does not exist!"
        }

        pip install -r $requirementsPath

        if ($LASTEXITCODE -ne 0) {
            Throw "`nFailed to Install New Dependencies!`nEXIT CODE: $LASTEXITCODE"
        } else {
            Write-Host "`nNew Dependencies Installed!" -ForegroundColor Green
        }

        Write-Host "`nUPDATE COMPLETED!" -ForegroundColor Green
    } catch {
        Write-Host "$($_.Exception.Message)`n`nUPDATE NOT COMPLETED!" -ForegroundColor Red
    }
} catch {
    Write-Host "`nFailed to Download Update`nERROR: $($_.Exception.Message)" -ForegroundColor Red
}

# Show exit confirmation
Write-Host "`nPress Enter to exit" -ForegroundColor Cyan -NoNewLine
Read-Host