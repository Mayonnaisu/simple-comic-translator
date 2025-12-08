## Other older versions
N/A

## v0.2.0
20/11/2025
1. Download repo snapshot instead of only model file
2. Remove onnx & onnxruntime from dependencies
3. Documentation is still a draft

## v0.4.0
23/11/2025
1. Remove ultralytics, sahi, & huggingface_hub from dependencies
2. Downgrade Python version from 3.12.0 to 3.11.0
3. Downgrade torch, torchvision, & numpy versions
4. Use PaddleOCR for detection instead of YOLO
5. Add installer, launcher, & updater
6. Add extra module/s
7. Improve console output
8. Add summarization of the translation [(to be removed?)](docs/workflow.md#5-translate-and-summarize-extracted-texts-with-gemini)
9. Add function to save translation & summary as text file
10. Add more content to documentations (in progress)
11. Improve error handling (in progress)
12. Add filtering (in progress)
13. Add logging
14. Add progress bar and only show certain outputs in debug mode
15. Add testing with GitHub Actions

### TODO
0. Add manga support
1. Add demo
2. Improve comments
3. Clean up, simplify, and optimize code
4. Upgrade PaddleOCR version to support PP-OCRv5 (tried but somehow I couldn't get it to work reliably and accurately, unlike the older version. \*Sigh\*)

## v0.5.0 (cancelled)
20/11/2025
> [!NOTE]
    <details>
        <summary>Why?</summary>
            <p>I intended to imitate PaddleOCR's built-in slicer so that I could just skip the detection stage and go straight to OCR. It did work, but there was a big problem. The problem was when deduplicating the overlapping OCR texts, the results were riddled with wrong texts from the split areas. It's because even though I had designed it to only use the text with the highest confidence among its duplicates, it still didn't guarantee that the text was not from the split area.</p>
            <p>That's when I started to check the PaddleOCR's built-in slicer code. It turned out that the way it works is similar to the v0.4.0 lol: detection on overlapping slices -> safe splitting original image -> text recoginition. The difference is that instead of just splitting the image horizontally like v0.4.0, PaddleOCR cuts the text areas out of the image.</p>
            <p>Someone with better programming skills probably can write a function to properly deduplicate the overlapping texts. But as of I'm now, I can't. That's why, after days of trying, I decided to just cancell it. Who knows, maybe someday I will be able to implement it.</p>
    </details>
1. Replace horizontal-slicing-with-overlap function with tiling-with-overlap function.
2. Improve deduplication to also calculate horizontal IoU
3. Still in trial (draft) stage basically