import os
import threading
import faulthandler
from tqdm import tqdm
import concurrent.futures
from loguru import logger
from manga_ocr import MangaOcr

from app.core.image_utils_pil import crop_out_box


faulthandler.enable()
lock = threading.Lock()


class MangaOCRRecognition:
    """
    A class to handle text extraction using Manga OCR.
    """
    def __init__(self, use_cpu: bool):
        """
        Initializes the Manga OCR model.

        :param use_cpu: Whether to use CPU for inference.
        """

        logger.info(f"Initializing Manga OCR model.")

        self.mocr = MangaOcr(force_cpu=use_cpu)

        logger.info("Manga OCR model initialized.")

    def run_mangaocr_on_detections(self, image: object, crop_name: str, detection: dict, upscaler: list[bool | int], output_dir: str, log_level: str):

        use_upscaler, upscale_ratio = upscaler

        with lock:
            box = detection["box"]
            xmin = box[0][0]
            ymin = box[0][1]
            xmax = box[2][0]
            ymax = box[2][1]

            cropped_img_resized = crop_out_box([xmin, ymin, xmax, ymax], image, [use_upscaler, upscale_ratio], output_dir, crop_name, log_level)

            text = self.mocr(cropped_img_resized)

            if text and text != "．．．":
                detection["original_text"] = text.strip()

                if log_level == "TRACE" and text != "":
                    logger.info(f"{text}")

                return detection


    def batch_threaded2(self, image: object, number: int, detections: list[dict], upscaler: list[bool | int], output_dir: str, log_level: str):
        """Manages thread pool for batch recognition"""

        all_results = []
        # Get the number of CPU threads and divide it by 2
        num_threads = int(os.cpu_count()/2)

        logger.info(f"\nExtracting texts with Manga OCR in {num_threads} threads.")

        # Use ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all images for processing
            future_to_path = {executor.submit(self.run_mangaocr_on_detections, image, f"crop{number}_{i:02d}.jpg", detection, upscaler, output_dir, log_level): detection for i, detection in enumerate(detections)}

            # Monitor progress and wait for all futures to complete
            for future in tqdm(concurrent.futures.as_completed(future_to_path), total=len(detections), desc="OCR"):
                result = future.result()
                if result:
                    all_results.append(result)

        # Return the populated, thread-safe results dictionary
        filtered_results = [result for result in all_results if result["original_text"] != ""]

        logger.success(f"Extracted {len(filtered_results)} texts.")

        return filtered_results