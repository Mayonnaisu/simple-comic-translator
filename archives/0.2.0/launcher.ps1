Write-Host "PowerShell $((Get-Host).Version.ToString())"

venv/Scripts/activate

python main.py --input ".\test\local\New folder"

# Show exit confirmation
Write-Host "`nPress Enter to exit" -ForegroundColor Cyan -NoNewLine
Read-Host