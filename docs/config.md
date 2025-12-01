## CONFIG OPTIONS

### "IMAGE_MERGE"
```jsonc
"enable": true                  // enable/disable including DETECTION & IMAGE_SPLIT
```

### "DETECTION"
```jsonc
"source_language": "korean",    // input language for PaddleOCR: "japan", "korean", "ch", etc.
"slice_height": 2000,           // height of each slice
"ocr_overlap": 0.2,             // overlap of each slice
"merge_y_threshold": 50,        // maximum vertical distance to merge detections
"merge_x_threshold": 100        // maximum horizontal distance to merge detections
```

### "IMAGE_SPLIT"
> [!NOTE]
> Split & slice are basically the same thing.
```jsonc
"max_height": 2000              // maximum height of each split
```

### "OCR"
```jsonc
"merge_y_threshold": 50,        // maximum vertical distance to merge ocr results
"merge_x_threshold": 100,       // maximum horizontal distance to merge ocr results
"slicer": {
    "enable": false,            // use PaddleOCR built-in slicer. useful when IMAGE_MERGE is disabled & PaddleOCR struggles to recognize texts
    "horizontal_stride": 1200,  // horizontal step size of the sliding window
    "vertical_stride": 400      // vertical step size of the sliding window
}
```

> [!TIP]
> For more info about PaddleOCR built-in slicer, see https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version2.x/ppocr/blog/slice.en.md.

### "TRANSLATION"
```jsonc
"target_language": "en",            // translation language
"gemini_model": "gemini-2.5-flash"  // Gemini model ID
```

> [!TIP]
> Visit https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions#gemini-auto-updated to see Gemini model IDs.

### "OVERLAY"
```jsonc
"font": {
  "min_size": 11,                   // minimum size of font
  "max_size": 40,                   // maximum size of font
  "path": "fonts/JetBrainsMonoNerdFont-Bold.ttf" // path to font file
}
```