<p align="center">
  <img width="256" height="256" alt="Simple Comic Translator" title="Simple Comic Translator" src="./assets/images/u1f609_u1f4a9.png" />
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
*   [DOWNLOAD](#download)
*   [INSTALLATION](#installation)
*   [CONFIGURATION](#configuration)
    *   [Required](#required)
    *   [Optional](#optional)
*   [USAGE](#usage)
*   [UPDATE](#update)
*   [LIMITATIONS](#limitations)
*   [FAQ](#faq)

## NOTICE
### <mark>Update & redownload config.json and prompt.yaml to get the latest features. For more info, see [CHANGELOG](CHANGELOG.md).</mark>

### All PowerShell scripts (.ps1) are only tested on Windows and may not be compatible with PowerShell Core run *directly* on other OSes.

### For advanced users, use this [guide](docs/README.md).

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
title="Tasteless T-Rex Meme" src="assets/images/stand-up-dinosaur.jpg" />
</p>

### Background
This is just a ~~shitty~~ simple app for translating comics in batch with Gemini. It can translate comic images in a folder recursively and save them to the corresponding output folder/subfolders with its [limitations](#limitations). Don't use this janky app! Instead, use these:

- [Manga Image Translator](https://github.com/zyddnys/manga-image-translator)
- [Comic Translate](https://github.com/ogkalu2/comic-translate)
- [BallonsTranslator](https://github.com/dmMaze/BallonsTranslator)
- [EasyScanlate](https://github.com/Liiesl/EasyScanlate)

However, if you insist on using my app, then proceed to the next section. You've been warned! Just don't expect much cuz it's intended to be "simpler" than those better alternatives or other programs not mentioned here (go search them on your own).

## WORKFLOW
Go to [here](docs/workflow.md).

## DEMO
Go to [here](docs/demo.md).

## DOWNLOAD
1. Click on the green button on the top.
2. Select "Download ZIP".
3. Right click on the downloaded .zip file.
4. Select "Extract Here" with WinRAR or 7-Zip.

## INSTALLATION
> [!IMPORTANT]
> **The installer only supports Windows 10 & 11.**
1. Open PowerShell as Administrator.
2. Change PowerShell execution policy by entering the command below:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```
3. Enter y or yes.
4. Close the PowerShell.
5. Right click on **installer.ps1**.
6. Select "Run with PowerShell".
7. Select "Yes" if UAC prompt pops up.
8. Wait until you get ${{\color{lightgreen}{\textsf{INSTALLATION COMPLETED!}}}}\$ message.
> [!TIP]
> If you get a warning when opening the installer, uncheck the option, then Open. If you don't do this, the script won't be able to run properly.
	<details>
		<summary>View image</summary>
			<p align="center">
				<img width=350 alt="Warning for Script"
	title="Warning for Script" src="https://github.com/user-attachments/assets/db276338-8c2a-4a87-88dd-017df8cef515" />
			</p>
	</details>

## CONFIGURATION
### Required
1. Open **.env** file with text/code editor (Notepad, VS Code, etc).
2. Paste your [Gemini API key](docs/api-keys.md#gemini) between the quotation marks.
3. Save.

For other available API keys, see [API Key References](docs/api-keys.md#google-ai).

### Optional
1. Open **config.json** with text/code editor.
2. Change the settings as you see fit.
3. Save.

For more info, see [config options](docs/config.md).

## USAGE
1. Right click on **launcher.ps1**.
2. Select "Run with PowerShell".
3. Select a folder containing your manga/hwa/hua.

## UPDATE
> [!WARNING]
> This updater will replace the old files with the newer ones, so make sure to back up the files you want to keep first. For more info, see [here](CHANGELOG.md).
>
> **Exclusions:**
> - config.json
> - prompt.yaml
> - filters/*

1. Right click on **updater.ps1** > Run with PowerShell.
2. Wait until you get ${{\color{lightgreen}{\textsf{UPDATE COMPLETED!}}}}\$ message.

## LIMITATIONS
1. It can't automatically detect the input language and only supports one language in each process. As a result, you need to manually specify the language in **config.json**.
2. Some texts, especially non-plain/styled texts, may not be recognized properly if at all.
3. Some unwanted texts may also be detected and recognized, making the result riddled with unnecessary texts and white rectangles.
4. Gemini itself is prone to throwing ["model overloaded" error](https://github.com/google-gemini/gemini-cli/issues/4360) & returning [`None`](https://github.com/googleapis/python-genai/issues/626) or incomplete response and [response with messed-up format](https://github.com/google-gemini/gemini-cli/issues/10972). When those happen, just retry it manually or increase `max_retries` in **config.json** for more automatic retries.

## FAQ
Go to [here](docs/faq.md).