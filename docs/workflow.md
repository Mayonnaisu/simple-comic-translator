## WORKFLOW
### 1. Merge images into One with [Pillow](https://github.com/python-pillow/Pillow) (optional)

### 2. Detect Text Areas with [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) (depends on step 1)
You may be wondering why I chose older version of PaddleOCR. It is because this version still has built-in slicing feature that's useful for extracting smaller texts.

### 3. Split Image Safely on Non-Text Areas with [Pillow](https://github.com/python-pillow/Pillow) (depends on step 1)

### 4. Extract Texts with [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)

### 5. Translate and Summarize Extracted Texts with [Gemini](https://github.com/googleapis/python-genai)
This stage is crucial as I designed it to send all extracted texts from one entire chapter to Gemini instead of the texts from only one page at a time. This is expected to make Gemini yield a better and more contextual translations.

This stage also requests Gemini to summarize the texts so that my app can send it back as additional context when translating the next chapter.

### 6. Redact Text Areas with [Pillow](https://github.com/python-pillow/Pillow)
#### Whitening (default)
Whitening is used by default because it's simpler and lighter, thus faster compared to inpainting. It also results in better readability as it overlays white box to speech bubble outlines and its surrounding background, in case the translated texts overflow from their speech bubbles. The downside is that it doesn't look as pretty and clean as inpainting.

#### Inpainting (TODO)

### 7 Overlay Translated Texts with [Pillow](https://github.com/python-pillow/Pillow)

### 8. Save to Corresponding Output Folders with [Pillow](https://github.com/python-pillow/Pillow)