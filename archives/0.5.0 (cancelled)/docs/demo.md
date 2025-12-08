## DEMO

> [!IMPORTANT]
>
> Tested on:
> - [Windows 11 25H2](#windows-11-25h2)
> - [Windows 11 22H2 in VirtualBox](#windows-11-22h2-in-virtualbox)
> - [Ubuntu 24 in WSL2](#ubuntu-24-in-wsl2)
> - [Ubuntu 25.10 (proot-distro) in Termux](#ubuntu-2510-proot-distro-in-termux)

### Windows 11 25H2


### Windows 11 22H2 in VirtualBox


### Ubuntu 24 in WSL2


### Ubuntu 25.10 (proot-distro) in Termux
```bash
# After installation, replace opencv with opencv-headless
pip uninstall opencv-python opencv-contrib-python opencv-python-headless -y

pip install numpy==1.26.4 opencv-python-headless opencv-contrib-python-headless
```

