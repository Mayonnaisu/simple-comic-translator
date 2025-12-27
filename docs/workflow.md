## WORKFLOW
### 1. Merge images into One with [Pillow](https://github.com/python-pillow/Pillow) (optional)
SCT merges all images in each subfolder into one respectively.

> [!NOTE]
> This step ensures that the text will be detected and recognized properly in later steps because it eliminates the split text areas from the original images, if there is any.

### 2. Detect Text Areas with [ogkalu/comic-text-and-bubble-detector](https://huggingface.co/ogkalu/comic-text-and-bubble-detector)
SCT detects text areas in order to find the areas that need to be cropped out for OCR step and avoided during the safe-splitting step.

> [!NOTE]
> Before the detection, I had to add **image-tiling-with-overlap+resizing** function because I found that this model can't accurately detect objects when the image resolution is not exactly 640x640 px.
>
> Since it will take too long time to process multiple 640x640 tiles, I decided to add option to use the original image width as the tile sizes. This is where the resizing comes into handy. The resizing will get trigerred when the tile sizes aren't equal to 640x640 px. As a result, there will be fewer tiles to process, hence the speed increase.

### 4. Extract Texts with [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
SCT extracts texts from each cropped-out text area.

> [!NOTE]
> Unlike the previously used PaddleOCR version, this version doesn't have the built-in slicer anymore. However, it's fine because the quality and resolution of the cropped-out image should already be good enough for it to accurately recognize.

### 3. Split Image Safely on Non-Text Areas with [Pillow](https://github.com/python-pillow/Pillow) (depends on step 1)
SCT splits the merged image into the specified height without overlap while avoiding the detected text areas.

> [!NOTE]
> Usually, the original images have some areas where the texts are split (talking about long-strip comics). This step prevents the overlaid text from also getting split. It's because it eliminates the situation where the program attempts to overlay the text to the non-existent part of area which only exists on the next image.

### 5. Translate and Summarize Extracted Texts with [Gemini](https://github.com/googleapis/python-genai)
SCT sends the extracted texts to Gemini for translation and summarization.

> [!NOTE]
> This stage is crucial as I designed it to send all extracted texts from one entire chapter to Gemini instead of the texts from only one page at a time. This is expected to make Gemini yield a better and more contextual translations.
>
> This stage also requests Gemini to summarize the texts so that the program can include it as additional context when translating the next chapter.

> [!IMPORTANT]
> I'm considering removing the summarization function because I found that it does nothing to improve the translation quality. 🤔

### 6. Redact Text Areas with [Pillow](https://github.com/python-pillow/Pillow)
SCT whitens text areas by simply overlaying white rectangle with offset on them.

> [!NOTE]
> Whitening is used because it's simpler and lighter, thus faster compared to inpainting. It also results in better readability in a way as it overlays bigger white boxes to the original text areas, in case the translated texts overflow from their original text areas. The downside is that it doesn't look as pretty and clean as inpainting.

### 7 Overlay Translated Texts with [Pillow](https://github.com/python-pillow/Pillow)
SCT overlays translated texts to the offset whitened areas while attempting to auto resize the fonts to fit into the areas.

> [!NOTE]
> The offset is necessary to make the area bigger so that the translated text, which is usually longer than the original text, can fit more nicely in the area.

### 8. Save to Corresponding Output Folders with [os.walk](https://docs.python.org/3.12/library/os.html#os.walk) + [pathlib.Path](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path)
Save the translated images to the corresponding output subfolders, maintaining the directory structure from the original directory.

> [!NOTE]
> By default, it will save the translated images to **\<input folder name\>-shitted** folder 💩😅.
