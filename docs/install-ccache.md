# Installing Ccache
> [!NOTE]
> For more info, see https://github.com/Mayonnaisu/simple-comic-translator/issues/3.

## Windows
### Installation
```powershell
# With WinGet
winget install --id Ccache.Ccache --source winget --exact
```

```powershell
# With Chocolatey
choco install ccache
```

### Configuration
- Restart the terminal

## Linux
### Installation
```bash
# For Debian/Ubuntu/Mint
sudo apt update
sudo apt install ccache
```
```bash
# For Red Hat/CentOS/Fedora
sudo yum install ccache

# or for newer Fedora systems
sudo dnf install ccache
```
```bash
# For Arch Linux
sudo pacman -S ccache
```

### Configuration
```bash
# Add ccache to PATH
echo 'export PATH="/usr/lib/ccache:$PATH"' >> ~/.bashrc

# Apply the changes
source ~/.bashrc
```

## macOS
### Installation
```zsh
# With Homebrew
brew install ccache
```

### Configuration
```zsh
# Add ccache to PATH
echo 'export PATH="$(brew --prefix)/opt/ccache/libexec:$PATH"' >> ~/.zshrc

# Apply the changes
source ~/.zshrc
```