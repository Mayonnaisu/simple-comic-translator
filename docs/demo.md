## DEMO

> [!IMPORTANT]
>
> Tested on:
> - [Windows 11 25H2](#windows-11-25h2)
> - [Ubuntu 25.10 (proot-distro) in Termux](#ubuntu-2510-proot-distro-in-termux)

### Windows 11 25H2
#### Configuration
```jsonc
// enable image merging
  "IMAGE_MERGE": {
    "enable": true
  }
```
```jsonc
// disable PaddleOCR's slicer
  "OCR": {
    "merge_y_threshold": 30,
    "merge_x_threshold": 100,
    "slicer": {
      "enable": false,
      "horizontal_stride": "original",
      "vertical_stride": 640
    }
  }
```

#### Result
<table align="center" width="400">
    <tbody>
        <tr>
        <h4 align="center">Manhua (Martial Peak)</h4>
        </tr>
        <tr>
            <td width="50%">
                <h4 align="center">Original</h4>
            </td>
            <td width="50%">
                <h4 align="center">Shitted</h4>
            </td>
        </tr>
        <tr>
            <td width="50%">
                <img alt="" title="" src="../assets/images/demo-1-1.webp"/>
            </td>
            <td width="50%">
                <img alt="" title="" src="../assets/images/demo-1-1-shitted.webp"/>
            </td>
        </tr>
        <tr>
            <td width="50%">
                <img alt="" title="" src="../assets/images/demo-1-2.webp"/>
            </td>
            <td width="50%">
                <table>
                <tr>
                    <td>
                    <img alt="" title="" src="../assets/images/demo-1-2a-shitted.webp"/>
                    </td>
                </tr>
                <tr>
                    <td>
                    <img alt="" title="" src="../assets/images/demo-1-2b-shitted.webp"/>
                    </td>
                </tr>
                </table>
            </td>
        </tr>
    </tbody>
</table>

Lol, the name is wrong, which is quite usual for machine translation. Then again, I only translated 1 chapter for demo purpose.

### Ubuntu 25.10 (proot-distro) in Termux
#### Post-installation
```bash
# Replace opencv with opencv-headless
pip uninstall opencv-python opencv-contrib-python opencv-python-headless -y

pip install numpy==1.26.4 opencv-python-headless opencv-contrib-python-headless
```

#### Configuration
```jsonc
// disable image merging
  "IMAGE_MERGE": {
    "enable": false
  }
```
```jsonc
// disable PaddleOCR's slicer
  "OCR": {
    "merge_y_threshold": 30,
    "merge_x_threshold": 100,
    "slicer": {
      "enable": false,
      "horizontal_stride": "original",
      "vertical_stride": 640
    }
  }
```

#### Result
<table align="center" width="600">
    <tbody>
        <tr>
        <h4 align="center">Manhwa (Hell is Other People)</h4>
        </tr>
        <tr>
            <td width="50%">
                <h4 align="center">Original</h4>
            </td>
            <td width="50%">
                <h4 align="center">Shitted</h4>
            </td>
        </tr>
        <tr>
            <td width="50%">
                <img alt="" title="" src="../test/remote/manhwa/RAW/030/03.jpeg"/>
            </td>
            <td width="50%">
                <img alt="" title="" src="../assets/images/demo-4-3-shitted.jpg"/>
            </td>
        </tr>
    </tbody>
</table>