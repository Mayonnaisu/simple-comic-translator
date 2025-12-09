## CONFIG OPTIONS

### IMAGE_MERGE
```jsonc
"enable": true                  // enable/disable including DETECTION & IMAGE_SPLIT
```

### DETECTION
```jsonc
"source_language": "korean",    // input language for PaddleOCR: "japan", "korean", "ch", "en", etc.
"slice_height": 2000,           // height of each slice
"det_overlap": 0.2,             // overlap of each slice
"merge_y_threshold": 30,        // maximum vertical distance to merge detections
"merge_x_threshold": 100        // maximum horizontal distance to merge detections
```

> [!TIP]
> For more language codes, see https://github.com/Mushroomcat9998/PaddleOCR/blob/main/doc/doc_en/multi_languages_en.md#5-support-languages-and-abbreviations. Idk which ones aren't supported by PP-OCRv4 tho.

### IMAGE_SPLIT
```jsonc
"max_height": 2000              // maximum height of each split
```

> [!NOTE]
> Split & slice are basically the same thing.

> [!TIP]
> If some texts are missed by PaddleOCR because they're too small in general, lower the `max_height` value.

### OCR
```jsonc
"merge_y_threshold": 30,        // maximum vertical distance to merge ocr results
"merge_x_threshold": 100,       // maximum horizontal distance to merge ocr results
"slicer": {
    "enable": false,            // use PaddleOCR built-in slicer
    "horizontal_stride": "original",  // horizontal step size of the sliding window: "original" (width) or number
    "vertical_stride": 1200      // vertical step size of the sliding window
}
```

> [!TIP]
> - PaddleOCR built-in slicer is useful when `IMAGE_MERGE` is disabled, & PaddleOCR struggles to recognize texts. For more info, see https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version2.x/ppocr/blog/slice.en.md.
>
> - Reduce `merge_threshold` value if there are nearby texts that shouldn't be merged, and vice versa.

### TRANSLATION
```jsonc
"target_language": "en",            // translation language
"gemini_model": "gemini-2.5-flash"  // Gemini model ID
```

> [!TIP]
> Visit https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions#gemini-auto-updated to see Gemini model IDs.

### OVERLAY
```jsonc
"font": {
  "min_size": 11,                   // minimum size of font
  "max_size": 40,                   // maximum size of font
  "path": "fonts/JetBrainsMonoNerdFont-Bold.ttf" // path to font file
}
```
