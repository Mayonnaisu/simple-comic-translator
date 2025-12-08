## WORKFLOW
### 1. Merge images into One with [Pillow](https://github.com/python-pillow/Pillow) (optional)
SCT merges all images in each subfolder into one respectively.

> [!NOTE]
> This step ensures that the text will be detected and recognized properly in later steps because it eliminates the split text areas from the original images.

### 2. Detect Text Areas with [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) (depends on step 1)
SCT detects texts in order to find the areas that need to be avoided during the splitting step.

> [!NOTE]
> Before the detection, I had to add image-slicing with overlap function because I found out that some detectors and OCR models I tried can't accurately detect or recognize objects when the image resolution is too large. One of them can't even detect object accurately if the image resolution is not exactly 640x640 px smh. 

### 3. Split Image Safely on Non-Text Areas with [Pillow](https://github.com/python-pillow/Pillow) (depends on step 1)
SCT splits the merged image into the specified height without overlap while avoiding the detected text areas.

### 4. Extract Texts with [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
SCT extracts texts from each split image.

> [!NOTE]
> You may be wondering why I chose the older version of PaddleOCR. It is because this version still has a built-in slicing feature that's useful for extracting smaller texts. The feature has annoying limitation tho. It will throw error if [the input image resolution is larger than 32k pixels](https://github.com/opencv/opencv/issues/7544) because it uses OpenCV, which is known for being unable to handle large images gracefully (as of now).
> 
> Besides the accuracy issue mentioned above, this is also why I decided to make the program split the merged image before OCR although PadlleOCR itself has a built-in slicer.

### 5. Translate and Summarize Extracted Texts with [Gemini](https://github.com/googleapis/python-genai)
SCT sends the extracted texts to Gemini for translation and summarization.

> [!NOTE]
> This stage is crucial as I designed it to send all extracted texts from one entire chapter to Gemini instead of the texts from only one page at a time. This is expected to make Gemini yield a better and more contextual translations.
>
> This stage also requests Gemini to summarize the texts so that the program can include it as additional context when translating the next chapter.

> [!IMPORTANT]
> I'm considering removing the summarization function because I found that it does nothing to improve the translation quality. 🤔

### 6. Redact Text Areas with [Pillow](https://github.com/python-pillow/Pillow)
SCT whitens text areas by simply overlaying white rectangle with offset/padding on them.

> [!NOTE]
> Whitening is used because it's simpler and lighter, thus faster compared to inpainting. It also results in better readability as it overlays bigger white boxes to the original text areas, in case the translated texts overflow from their original text areas. The downside is that it doesn't look as pretty and clean as inpainting.

### 7 Overlay Translated Texts with [Pillow](https://github.com/python-pillow/Pillow)
SCT overlays translated texts to the padded whitened areas while attempting to auto resize the fonts to fit into the areas.

> [!NOTE]
> The padding/offset is necessary to make the area bigger so that the translated text, which is usually longer than the original text, can fit more nicely in the area.
>
> Btw, during the earlier stage of development, there was a time when I made the program to only (1) merge images, then (2) slice the merged image with overlap before (3) feeding it to OCR, & (4) translate OCR results before (5) overlaying the text to the original images. It had fewer steps, and thus was faster than the current pipeline.
>
> There was one critical issue tho. Usually, the original images have some areas where the texts are split (talking about long-strip comic). This caused the overlaid text to also get split because the program tried to overlay the text to the non-existent part of area which only exists on the next image.

### 8. Save to Corresponding Output Folders with [Pillow](https://github.com/python-pillow/Pillow)
Save the translated images to the corresponding output subfolders, maintaining the directory structure from the original directory.

> [!NOTE]
> By default, it will save the translated images to **\<input folder name\>-shitted** folder 💩😅.