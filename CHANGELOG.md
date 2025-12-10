## Other older versions
N/A

## v0.2.0
20/11/2025
1. Download repo snapshot instead of only model file
2. Remove `onnx` & `onnxruntime` from dependencies
3. Documentation is still a draft

## v0.4.0
23/11/2025
## v0.4.1
10/12/2025
1. Remove ultralytics, sahi, & huggingface_hub from dependencies
2. Downgrade Python version from 3.12.0 to 3.11.0
3. Downgrade `torch`, `torchvision`, & `numpy` versions
4. Use PaddleOCR for detection instead of YOLO
5. Add installer, launcher, & updater
6. Add extra module/s
7. Improve console output
8. Add summarization of the translation [(to be removed?)](docs/workflow.md#5-translate-and-summarize-extracted-texts-with-gemini)
9. Add function to save translation & summary as text file
10. Add more content to documentations
11. Improve error handling (in progress)
12. Add filtering (in progress)
13. Add logging (in progress)
14. Add progress bar and only show certain outputs in debug mode
15. Add testing with GitHub Actions
16. Add demo
17. Upgrade `paddlepaddle` for patching vulnerabilities in transitive dependencies: https://github.com/Mayonnaisu/simple-comic-translator/commit/cd167d36acef6a041aaeeaf0e3a6a7cb8ab36aca

### TODO
1. Add manga support
2. Improve comments
3. Clean up, simplify, and optimize code
4. Upgrade PaddleOCR version to support PP-OCRv5 (tried but somehow I couldn't get it to work reliably and accurately, unlike the older version. \*Sigh\*)