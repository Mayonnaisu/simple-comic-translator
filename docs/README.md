<p align="center">
  <img width="256" height="256" alt="Simple Comic Translator" title="Simple Comic Translator" src="../assets/images/u1f4a9_u1f913.png" />
    <h1 align="center">Simple Comic Translator 💩</h2>
    <p align="center">Translate comic and manga/hwa/hua in batch.</p>
</p>

<p align="center">
<a href="https://github.com/Mayonnaisu/simple-comic-translator/blob/main/LICENSE">
  <img src="https://img.shields.io/github/license/Mayonnaisu/simple-comic-translator"/></a>
</p>

[![Test App](https://github.com/Mayonnaisu/simple-comic-translator/actions/workflows/test-app.yml/badge.svg)](https://github.com/Mayonnaisu/simple-comic-translator/actions/workflows/test-app.yml)

## STATUS
> [!WARNING]
> - Under construction 🛠️
> - Unstable ⚠️
> - Not thoroughly tested yet ⁉️

## DIRECTORY
*   [NOTICE](#notice)
*   [ABOUT](#about)
    *   [Full Name](#full-name)
    *   [Shorter Names](#shorter-names)
    *   [Background](#background)
*   [WORKFLOW](#workflow)
*   [DEMO](#demo)
*   [PREREQUISITES](#prerequisites)
*   [DOWNLOAD](#download)
*   [INSTALLATION](#installation)
*   [CONFIGURATION](#configuration)
    *   [Required](#required)
    *   [Optional](#optional)
*   [USAGE](#usage)
*   [UPDATE](#update)
*   [LIMITATIONS](#limitations)
*   [EXTRA INFO](extra-info)
    *   [How to Get Gemini API Key](#how-to-get-gemini-api-key)
    *   [FAQ](#faq)

## NOTICE
### <mark>Version 0.5.0 has been released! To upgrade from the previous version, see https://github.com/Mayonnaisu/simple-comic-translator/issues/7.</mark>

## ABOUT
### Full Name
[***THAT TIME I GOT REINCARNATED AS A SCRIPT KIDDIE FOR THE SAKE OF CREATING THIS NOT-SO-SIMPLE COMIC TRANSLATOR WITH THE HELP OF MY UNRELIABLE SYSTEM (GEMINI)***](https://github.com/Mayonnaisu/simple-comic-translator) 😂

> *Me: "System, how to extract text from image with PaddleOCR?"<br>*
> *System: "To extract text from image with PaddleOCR- Oops, something went wrong with this response."*<br>
> *Me: "...."*<br>
> 
> *\*\*A few moments later\*\**
>
> *Me: "Alright, translate this OCR results to English."*<br>
> *System: ["503 UNAVAILABLE. {'error': {'code': 503, 'message': 'The model is overloaded. Please try again later.', 'status': 'UNAVAILABLE'}}"](https://github.com/google-gemini/gemini-cli/issues/4360)*<br>
> *Me: "WTF!"*

### Shorter Names
[***SCT***](#shorter-names)<br>
Read:<br>
-> "S-C-T"<br>
-> "ess-see-tee"<br>
-> "Shitty" 💩

<p align="center">
    <img width=200 alt="Tasteless T-Rex Meme"
title="Tasteless T-Rex Meme" src="../assets/images/stand-up-dinosaur.jpg" />
</p>

### Background
This is just a ~~shitty~~ simple app for translating comics in batch with Gemini. It can translate comic images in a folder recursively and save them to the corresponding output folder/subfolders with its [limitations](#limitations). Don't use this janky app! Instead, use these:

- [Manga Image Translator](https://github.com/zyddnys/manga-image-translator)
- [Comic Translate](https://github.com/ogkalu2/comic-translate)
- [BallonsTranslator](https://github.com/dmMaze/BallonsTranslator)
- [EasyScanlate](https://github.com/Liiesl/EasyScanlate)

However, if you insist on using my app, then proceed to the next section. You've been warned! Just don't expect much cuz it's intended to be "simpler" than those better alternatives or other programs not mentioned here (go search them on your own).

## WORKFLOW
Go to [here](workflow.md).

## DEMO
Go to [here](demo.md).

## PREREQUISITES
- Git
- Python 3.11 or 3.12
- Microsoft C++ Build Tools (for Windows)
- Ccache ([optional](install-ccache.md))

## DOWNLOAD
```powershell
git clone "https://github.com/Mayonnaisu/simple-comic-translator"
```

## INSTALLATION
```powershell
# Create virtual environment
python -m venv venv

# Activate it
## For Windows
venv/Scripts/activate
## For Linux & macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements-lock.txt
```

## CONFIGURATION
### Required
1. Get your [Gemini API key](#how-to-get-gemini-api-key).
2. Create **.env** file in the program root directory:
```powershell
# powershell/bash/zsh/etc
echo "GEMINI_API_KEY='YourGeminiAPIkey'" > .env
```

### Optional
1. Open **config.json**.
2. Change the settings as you see fit.
3. Save.

For more info, see [config options](config.md).

## USAGE
```powershell
# Activate venv
## For Windows
venv/Scripts/activate
## For Linux & macOS
source venv/bin/activate

# Run with required argument only
python main.py --input "YOUR/COMIC/FOLDER/PATH"

# For more info
python main.py --help
```

## UPDATE
```powershell
# Update local repo
git pull

# Activate venv
## For Windows
venv/Scripts/activate
## For Linux & macOS
source venv/bin/activate

# Install new dependencies
pip install -r requirements-lock.txt
```

## LIMITATIONS
1. It can't automatically detect the input language and only supports one language in each process. As a result, you need to manually specify the language in **config.json**.
2. Some texts, especially non-plain/styled texts, aren't recognized properly if at all.
3. Some unwanted texts are also detected and recognized, making the result riddled with unnecessary texts and white rectangles.
4. Gemini itself is prone to throwing ["model overloaded" error](https://github.com/google-gemini/gemini-cli/issues/4360) & returning [`None`](https://github.com/googleapis/python-genai/issues/626) or incomplete response and [response with messed-up format](https://github.com/google-gemini/gemini-cli/issues/10972). When those happens, just retry it manually or increase `max_retries` in **config.json** for automatic retries.

## EXTRA INFO
### How to Get Gemini API Key
1. Visit https://aistudio.google.com/app/apikey.
2. Accept the Terms and Conditions.
3. Click "Create API key".
4. Name your key.
5. Choose project > Create project.
6. Select the newly created project.
7. Click "Create key".
8. Click the code in the "Key" column.
9. Click "Copy key".
> [!TIP]
> Gemini API Free Tier has rate limits, see: https://ai.google.dev/gemini-api/docs/rate-limits.
>
> **To check your quota:**
> 1. Visit https://aistudio.google.com/app/usage
> 2. Make sure you are on the right account & project.
> 2. Click "Open in Cloud Console" on the bottom.
> 3. Scroll down > Click "Quotas & System Limits".
> 4. Scroll down > You will see your model quota usage on the top result. If you don't see it, use Filter to search it.
>
> For example: 
    <details>
        <summary>View image</summary>
            <p align="center">
                <img alt="Gemini Free Tier Quota"
    title="Gemini Free Tier Quota" src="../assets/images/gemini-quota.png" />
            </p>
    </details>

### FAQ
Go to [here](faq.md).