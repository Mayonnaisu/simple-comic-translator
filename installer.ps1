# Change global preference for all errors to terminate the process
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $True

# temporarily set the policy to 'Bypass' for the current process
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Suppress the default progress bar because it slows down process in stock PowerShell (5.1). See https://github.com/PowerShell/PowerShell/issues/2138.
$ProgressPreference = 'SilentlyContinue'

# Define separate script for installing SCT dependencies in a new window later
$DependencyInstallerPath = ".\temp\dependency-installer.ps1"

$DependencyInstaller = @'
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $True
$host.PrivateData.ErrorForegroundColor = "Red"

$LogErrorInstallDependencyPath = ".\temp\log_errors-install-dependency.txt"
Start-Transcript -Path $LogErrorInstallDependencyPath

Write-Host "`n$PWD"

# Install Python 3.12.0
try {
    Write-Host "`nInstalling Python 3.12.0" -ForegroundColor Yellow

    pyenv --version

    pyenv install 3.12.0

    pyenv global 3.12.0

    if ($LASTEXITCODE -ne 0) {
        Throw "`nFailed to Install Python 3.12.0!`nEXIT CODE: $LASTEXITCODE"
    }
    
    pyenv versions

    python --version

    if ($? -eq $true) {
        where.exe python
    }
} catch {
    Write-Host "`nERROR: $($_.Exception.Message)"
    exit 1
}
Write-Host "`nPython 3.12.0 Installed." -ForegroundColor DarkGreen

# Set Up Python Virtual Environment
try {
    Write-Host "`nSetting Up Python Virtual Environment..." -ForegroundColor Yellow

    python -m venv venv

    if (Test-Path -Path $LogErrorInstallDependencyPath) {
        $LogErrorInstallDependency = Get-Content -Path $LogErrorInstallDependencyPath

        if ($LogErrorInstallDependency -match "No module named") {
            Throw "Failed to Create Virtual Environment!"   
        }
    }

    .\venv\Scripts\Activate.ps1 -ErrorAction Stop 
} catch {
    Write-Host "`nERROR: $($_.Exception.Message)"
    exit 2
}
Write-Host "`nPython Virtual Environment Created & Activated." -ForegroundColor DarkGreen

# Install SCT Dependencies
$requirementsPath = ".\requirements-lock.txt"

try {
    Write-Host "`nInstalling SCT Dependencies..." -ForegroundColor Yellow

    if (-not (Test-Path -Path $requirementsPath)) {
        Throw "Path '$requirementsPath' does not exist!"
    }

    pip install -r $requirementsPath

    if ($LASTEXITCODE -ne 0) {
        Throw "`nFailed to Install SCT Dependencies!`nEXIT CODE: $LASTEXITCODE"
    }
} catch {
    Write-Host "`nERROR: $($_.Exception.Message)"
    exit 3
}
Write-Host "`nSCT Dependencies Installed." -ForegroundColor DarkGreen

Stop-Transcript

exit 0
'@

# Define .env file content
$envFile = @"
GEMINI_API_KEY=''
"@

# Start the installation
try {
    # Clear previous errors
    $Error.Clear()

    $LogErrorInstallDependencyPath = ".\temp\log_errors-install-dependency.txt"
    if (Test-Path -Path $LogErrorInstallDependencyPath -PathType Leaf) {
        Remove-Item -Path $LogErrorInstallDependencyPath -Force
    }

    # Import module/s
    Import-Module ".\app\extra\downloader.psm1"

    # Display PowerShell version & start message
    Write-Host "PowerShell $((Get-Host).Version.ToString())"

    Write-Host "`nStarting Installer..." -ForegroundColor Yellow

    # Create folder, dependency-installer.ps1, & .env file
    New-Item -Path ".\temp" -ItemType Directory -Force

    Set-Content -Path $DependencyInstallerPath -Value $DependencyInstaller

    Set-Content -Path ".\.env" -Value $envFile

    # Install Microsoft C++ Build Tools
    Write-Host "`nInstalling Microsoft C++ Build Tools..." -ForegroundColor Yellow

    $MsixBundleUrl = "https://github.com/microsoft/winget-cli/releases/latest/download/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
    $MsixBundlePath = ".\temp\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"

    if (Test-Path $MsixBundlePath) {
        Write-Host "`nWinGet Already Exists at '$MsixBundlePath'. Skipping Download."
    } else {
        Write-Host "`nWinGet Not Found at '$MsixBundlePath'.`n`nDownloading from '$MsixBundleUrl'..."
        try {
            Start-ResumableBitsDownload -JobName "WinGet" -SourceUrl $MsixBundleUrl -DestinationPath $MsixBundlePath

            Write-Host "`nWinGet Downloaded Successfully to '$MsixBundlePath'."
        } catch {
            Throw "`nFailed to Download WinGet!`nERROR: $($_.Exception.Message)"
        }
    }

    $DependencyZipUrl = "https://github.com/microsoft/winget-cli/releases/latest/download/DesktopAppInstaller_Dependencies.zip"
    $DependencyZipPath = ".\temp\DesktopAppInstaller_Dependencies.zip"

    if (Test-Path $DependencyZipPath) {
        Write-Host "`nWinGet Dependencies Already Exists at '$DependencyZipPath'. Skipping Download."
    } else {
        Write-Host "`nWinGet Dependencies Not Found at '$DependencyZipPath'.`n`nDownloading from '$DependencyZipUrl'..."
        try {
            Start-ResumableBitsDownload -JobName "WinGet-Depedencies" -SourceUrl $DependencyZipUrl -DestinationPath $DependencyZipPath

            Write-Host "`nWinGet Dependencies Downloaded Successfully to '$DependencyZipPath'."
        } catch {
            Throw "`nFailed to Download WinGet Dependencies!`nERROR: $($_.Exception.Message)"
        }
    }

    $DependencyFolder = ".\temp\DesktopAppInstaller_Dependencies"

    try {
        Write-Host "`nInstalling WinGet..."

        $OSArchitecture = (Get-CimInstance -ClassName Win32_OperatingSystem).OSArchitecture

        if ($OSArchitecture -eq "ARM64") {
            $DependencyPath = "$DependencyFolder\arm64"
        } elseif ($OSArchitecture -eq "64-bit") {
            $DependencyPath = "$DependencyFolder\x64"
        } elseif ($OSArchitecture -eq "32-bit") {
            $DependencyPath = "$DependencyFolder\x86"
        } else {
            $DependencyPath = "$DependencyFolder\x64"
        }

        Expand-ArchiveWithProgress -ArchivePath $DependencyZipPath -DestinationPath $DependencyFolder

        $Dependencies = Get-ChildItem -Path $DependencyPath -Filter "*.appx*" | Select-Object -ExpandProperty FullName

        Add-AppxPackage -Path $MsixBundlePath -DependencyPath $Dependencies -Confirm:$False

        winget upgrade --accept-source-agreements

        Write-Host "`nWinGet Installed Successfully."
    } catch {
        Throw "`nFailed to Install WinGet!`nERROR: $($_.Exception.Message)"
    }

    try {
        Write-Host "`nInstalling Microsoft Visual Studio Build Tools & Its Components..."

        $myOS = systeminfo | findstr /B /C:"OS Name"

        if ($myOS.Contains("Windows 11")) {
            winget install Microsoft.VisualStudio.2022.BuildTools --force --override "--wait --passive --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows11SDK.26100" --accept-source-agreements --accept-package-agreements
        } else {
            winget install Microsoft.VisualStudio.2022.BuildTools --force --override "--wait --passive --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows10SDK" --accept-source-agreements --accept-package-agreements  
        }

        if ($LASTEXITCODE -ne 0) {
            Throw "Microsoft Visual Studio Build Tools Installer Failed!`nEXIT CODE: $LASTEXITCODE."
        } else {
            Write-Host "`nMicrosoft C++ Build Tools Installed Successfully." -ForegroundColor DarkGreen
        }
    } catch {
        Throw "`nFailed to Install Microsoft C++ Build Tools!`nERROR: $($_.Exception.Message)"
    }

    # Install Ccache
    try {
        Write-Host "`nInstalling Ccache..." -ForegroundColor Yellow

        winget install --id Ccache.Ccache --source winget --exact --force

        Write-Host "`nCcache Installed Successfully." -ForegroundColor DarkGreen
    } catch {
        Throw "`nFailed to Install Ccache!`nERROR: $($_.Exception.Message)"
    }

    # Install Pyenv Windows
    try {
        Write-Host "`nChecking Pyenv Windows..." -ForegroundColor Yellow

        pyenv --version

        Write-Host "`nPyenv Windows Already Installed." -ForegroundColor Green
    } catch [System.Management.Automation.CommandNotFoundException] {
        Write-Host "`nPyenv Windows Not Installed." -ForegroundColor Magenta

        try {
            Write-Host "`nInstalling Pyenv Windows..." -ForegroundColor Yellow

            $pathToadd = "$env:USERPROFILE\.pyenv\pyenv-win\bin;$env:USERPROFILE\.pyenv\pyenv-win\shims"

            $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')

            [Environment]::SetEnvironmentVariable('Path', "$pathToadd;$userPath", 'User')

            $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

            if ($isAdmin) {
                $systemPath = [Environment]::GetEnvironmentVariable('Path', 'Machine')

                [Environment]::SetEnvironmentVariable('Path', "$pathToadd;$systemPath", 'Machine')
            }

            Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./temp/install-pyenv-win.ps1"; &"./temp/install-pyenv-win.ps1" -ErrorAction Stop

            Write-Host "`nPyenv Windows Installed Successfully." -ForegroundColor DarkGreen
        } catch {
            Throw "$($_.Exception.Message)"
        }
    } catch {
        Throw "`nFailed to Install Pyenv Windows!`nERROR: $($_.Exception.Message)"
    }

    # Since it's required to reopen PowerShell after installing Pyenv Windows, I'll just launch PowerShell in a new window to install Python 3.12.0 with Pyenv, set up Python virtual environment, & install SCT dependencies.
    try {
        Write-Host "`nInstalling Python, Setting Up Python Virtual Environment, & Installing SCT Dependencies..." -ForegroundColor Yellow

        $taskName = "Install-SCT-Dependencies"
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(30)
        $taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -Command &'$DependencyInstallerPath' | Out-String -Stream | Write-Host" -WorkingDirectory $PWD

        Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $taskSettings -Description "temporary task to install SCT dependencies." -Force

        $scheduledTask = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop

        Start-ScheduledTask -TaskName $taskName

        while ($scheduledTask.State -ne 'Running') {
            Start-Sleep -Seconds 5
            Write-Host "`nSTATUS: $($scheduledTask.State) | Starting scheduled task..."
            $scheduledTask = Get-ScheduledTask -TaskName $taskName
        }

        Write-Host "Scheduled task '$taskName' started. Waiting for completion..."

        while ($scheduledTask.State -eq 'Running') {
            Start-Sleep -Seconds 5
            $scheduledTask = Get-ScheduledTask -TaskName $taskName
        }

        if ($scheduledTask.State -ne 'Running') {
            Write-Host "Scheduled task '$taskName' completed. Final state: $($scheduledTask.State)`n"
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        } else {
            Write-Host "Scheduled task '$taskName' started. Waiting for completion..."
            while (($scheduledTask.State -eq 'Running')) {
                Start-Sleep -Seconds 5
                $scheduledTask = Get-ScheduledTask -TaskName $taskName
            }
            Write-Host "Scheduled task '$taskName' completed. Final state: $($scheduledTask.State)`n"
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        }

        if (Test-Path -Path $LogErrorInstallDependencyPath) {
            $LogErrorInstallDependency = Get-Content -Path $LogErrorInstallDependencyPath
            $LogErrorInstallDependency
            $ErrorMatch = $LogErrorInstallDependency -notmatch "log_error"
            if ($ErrorMatch -match "Error") {
                Throw "Failed to Install Python, Create Virtual Environment, & Install SCT Dependencies."
            } else {
                Write-Host "`nPython Installed, Virtual Environment Created, & SCT Dependencies Installed Successfully." -ForegroundColor DarkGreen
            }
        }

        Remove-Item -Path $DependencyInstallerPath -Force
    } catch {
        Throw "`nERROR: $($_.Exception.Message)"
    }

    Write-Host "`nINSTALLATION COMPLETED!" -ForegroundColor Green
} catch {
    Write-Host "`n$($_.Exception.Message)`n`nINSTALLATION NOT COMPLETED!" -ForegroundColor Red
    # Save the contents of the $Error variable to a text file
    $ErrorLogPath = ".\temp\log_errors-install.txt"

    $Error | Out-File -FilePath $ErrorLogPath
}

# Show exit confirmation
Write-Host "`nPress Enter to exit" -ForegroundColor Cyan -NoNewLine
Read-Host