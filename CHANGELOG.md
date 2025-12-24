## Other older versions
N/A

## v0.2.0
20/11/2025
1. Download repo snapshot instead of only model file
2. Remove `onnx` & `onnxruntime` from dependencies
3. Documentation is still a draft

## v0.4.0
23/11/2025
1. Remove `ultralytics`, `sahi`, & `huggingface-hub` from dependencies
2. Downgrade Python version from 3.12.0 to 3.11.0
3. Downgrade `torch`, `torchvision`, & `numpy` versions
4. Use PaddleOCR for detection instead of YOLO
5. Add installer, launcher, & updater
6. Add extra module/s
7. Improve console output
8. Add summarization of the translation ([to be removed?](docs/workflow.md#5-translate-and-summarize-extracted-texts-with-gemini))
9. Add function to save translation & summary as text file
10. Add more content to documentations
11. Add filtering
12. Add logging
13. Add progress bar and only show certain outputs in debug mode
14. Add testing with GitHub Actions
15. Add demo

## v0.4.1
10/12/2025
17. Upgrade `paddlepaddle` for patching vulnerabilities in transitive dependencies ([cd167d3](https://github.com/Mayonnaisu/simple-comic-translator/commit/cd167d36acef6a041aaeeaf0e3a6a7cb8ab36aca))
18. Add Ccahe installation

## v0.5.0
23/12/2025
1. Upgrade Python version to 3.12
2. Add `torch`, `onnxruntime`, `huggingface-hub`, & `manga-ocr` to dependencies
3. Upgrade `numpy` version
4. Use dedicated detection model ([ogkalu/comic-text-and-bubble-detector](https://huggingface.co/ogkalu/comic-text-and-bubble-detector))
5. Add manga support with [manga-ocr](https://github.com/kha-white/manga-ocr)
6. Upgrade PaddleOCR to support PP-OCRv5 model (slower than the older version & doesn't have the built-in slicer anymore :/)
7. Replace **horizontal-slicing-with-overlap** with **tiling-with-overlap+resizing** function for detection pre-processing
8. Replace **safe-splitting** with **text-area-cropping+upscaling** function for OCR pre-processing

### TODO
1. Improve comments
2. Clean up, simplify, and optimize code
3. Improve error handling (in progress)
4. Improve filtering (in progress)
5. Improve logging (in progress)