<p align="center">
  <img width="256" height="256" alt="Simple Comic Translator" title="Simple Comic Translator" src="" />
    <h1 align="center">Simple Comic Translator</h2>
    <p align="center">Translate comic and manga/hwa/hua in batch.</p>
</p>

<p align="center">
<a href="https://github.com/Mayonnaisu/page-downloader/blob/main/LICENSE">
  <img src="https://img.shields.io/github/license/Mayonnaisu/page-downloader"/></a>
</p>

## 📂 Directory
*   [NOTICE](#notice)
*   [ABOUT](#about)
    *   [Full Name](#full-name)
    *   [Background](#background)
*   [DOWNLOAD](#download)
    *   [Download Zip](#method-1-download-zip)
    *   [Clone Repo](#method-2-clone-repo)
*   [INSTALLATION](#installation)
    *   [Installer](#installer)
    *   [CLI](#cli)
*   [CONFIGURATION](#configuration)
    *   [Required](#required)
    *   [Optional](#optional)
*   [USAGE (CPU MODE)](#usage-cpu-mode)
*   [USAGE (GPU MODE)](#usage-gpu-mode)
*   [UPDATE](#update)
*   [EXTRA INFO](extra-info)

## ABOUT
### Full Name
***THAT TIME I GOT REINCARNATED AS A SCRIPT KIDDY FOR THE SAKE OF CREATING THIS NOT-SO-[SIMPLE COMIC TRANSLATOR](https://github.com/Mayonnaisu/simple-comic-translator) WITH THE HELP OF MY UNRELIABLE SYSTEM (GEMINI)*** 😂

> *Me: "System, how to extract text from image with PaddleOCR?"<br>*
> *System: "To extract text from image with PaddleOCR... Oops, something went wrong with this response."*<br>
> *Me: "...."*<br>
> 
> *\*\*A few moments later\*\**
>
> *Me: "Alright, translate this OCR results to English."*<br>
> *System: ["503 UNAVAILABLE. {'error': {'code': 503, 'message': 'The model is overloaded. Please try again later.', 'status': 'UNAVAILABLE'}}"](https://github.com/google-gemini/gemini-cli/issues/4360)*<br>
> *Me: "WTF!"*

### Background
This is just a simple app for translating comic in batch with Gemini. It can translate comic images in a folder recursively and save them to the corresponding output folder. Don't use this janky app! Instead, use these:

- [Manga Image Translator](https://github.com/zyddnys/manga-image-translator)
- [Manga Image Translator Rust](https://github.com/frederik-uni/manga-image-translator-rust)
- [Comic Translate](https://github.com/ogkalu2/comic-translate)
- [BallonsTranslator](https://github.com/dmMaze/BallonsTranslator)
- [EasyScanlate](https://github.com/Liiesl/EasyScanlate)

However, if you insist on using my app, then proceed to the next section. You've been warned! Just don't expect much cuz it's intended to be "simpler" than those better alternatives or other programs not mentioned here (go search them on your own).

## WORKFLOW
### 1. Download Necessary Models


### 2. Merge images into One

### 3. Detect Text Areas with [YOLOv8](https://github.com/ultralytics/ultralytics) + [SAHI](https://github.com/obss/sahi)
Model: [ogkalu/comic-speech-bubble-detector-yolov8m](https://huggingface.co/ogkalu/comic-speech-bubble-detector-yolov8m)

### 4. Split Image Safely on Non-Text Areas

### 5. Extract Texts with [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
You may be wondering why I chose older version of PaddleOCR. It is because this version still has built-in slicing feature that's useful for extracting smaller texts.

### 6. Merge Nearby Boxes from OCR Results

### 7. Translate Extracted Texts with [Gemini](https://github.com/googleapis/python-genai)
This stage is crucial as I designed it to send all extracted texts from one entire chapter to Gemini instead of the texts from only one page at a time. This is expected to make Gemini yield a better and more contextual translations.

This stage also requests Gemini to summarize the texts so that my app can send it back as additional context when translating the next chapter.

### 8. Redact Text Areas
#### Whitening (default)
Whitening is used by default because it's simpler and lighter, thus faster compared to inpainting. It also results in better readability as it overlays white box to speech bubble outlines and its surrounding background, in case the translated texts overflow from their speech bubbles. The downside is that it doesn't look as pretty and clean as inpainting.

#### Inpainting
Model: [ogkalu/aot-inpainting](https://huggingface.co/ogkalu/aot-inpainting)

### 9 Overlay Translated Texts

### 10. Save to Corresponding Output Folders

## INSTALLATION
### Method 1: Download Zip
### Method 2: Clone Repo

## INSTALLATION
### Method 1: Installer
> [!TIP]
> If you get a warning when opening the installer, uncheck the option, then Open. If you don't do this, the script won't be able to run properly.
	<details>
		<summary>View image</summary>
			<p align="center">
				<img width=350 alt="Warning for Script"
	title="Warning for Script" src="https://github.com/user-attachments/assets/db276338-8c2a-4a87-88dd-017df8cef515" />
			</p>
	</details>

### Method 2: CLI
```powershell
# Create virtual environment
python -m venv venv

# Activate it
## For Windows
venv/Scripts/activate
## For Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## USAGE
### Method 1: Launcher
1. Right click on **launcher.ps1**.
2. Select "Run with PowerShell".
3. Select a folder containing your manga/hwa/hua.


### Method 2: CLI
```powershell
python main.py --input "YOUR/MANGA/FOLDER/PATH"
```

How to change detector, ocr, translator, etc, you ask? You can't, unless you modify the source code yourself. Or just use the aforementioned alternatives.