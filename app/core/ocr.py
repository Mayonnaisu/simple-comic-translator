import os
import logging
import threading
import numpy as np
import faulthandler
from tqdm import tqdm
import concurrent.futures
from loguru import logger
from manga_ocr import MangaOcr
from paddleocr import PaddleOCR

from app.core.image_utils import crop_out_box_pil

# suppress PaddleOCR's verbose logging
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = 'True'
os.environ['FLAGS_log_level'] = '3'
logging.getLogger("ppocr").setLevel(logging.ERROR)

faulthandler.enable()

lock = threading.Lock()
all_results = []

class PaddleOCRRecognition:
    """
    A class to handle text extraction using PaddleOCR.
    """
    def __init__(self, ocr_version: str, language: str, confidence_threshold: float, use_gpu: bool):
        """
        Initializes the PaddleOCR model.
        :param language: The language for OCR (e.g., 'japan', 'korean', 'ch', 'en', etc).
        :param device: Device to use for inference.
        """
        logger.info(f"Initializing PaddleOCR model for language: {language}...")

        self.confidence_threshold = confidence_threshold

        self.ppocr = PaddleOCR(
            ocr_version=ocr_version,
            lang=language,
            device='gpu:0' if use_gpu else 'cpu',
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

        logger.info("PaddleOCR model initialized.")

    def run_paddleocr_on_detections(self, image: object, crop_name: str, detection: dict, resizer: list[bool | int], output_dir: str, log_level: str):
        """Runs PaddleOCR on slices and adjusts coordinates to original image space."""

        with lock:
            try:
                use_resizer, resize_width = resizer

                box = detection["box"]

                xmin = box[0][0]
                ymin = box[0][1]
                xmax = box[2][0]
                ymax = box[2][1]

                cropped_img_resized = crop_out_box_pil([xmin, ymin, xmax, ymax], image, [use_resizer, resize_width], output_dir, crop_name, log_level)

                result = self.ppocr.predict(
                    np.array(cropped_img_resized)
                )

                recognized_text = ""
                avg_conf = 0
                if result:
                    for line in result:
                        # Filter out lower confidence
                        confidence = line['rec_scores']
                        confidence_number = len(confidence)
                        if confidence_number > 0:
                            avg_conf = sum([c for c in confidence]) / confidence_number
                        else:
                            avg_conf = 0

                        if avg_conf < self.confidence_threshold:
                            continue

                        text = line['rec_texts']
                        recognized_text = " ".join(text)

                    detection["original_text"] = recognized_text.strip()

                    detection["text_confidence"] = avg_conf

                    if log_level == "TRACE" and recognized_text != "":
                        logger.debug(f"({avg_conf:.2f}) {recognized_text}")

                    return detection
            except Exception as e:
                logger.error(f"Error processing image: {e}")

    def batch_threaded(self, image: object, number: int, detections: list[dict], resizer: list[bool | int], output_dir: str, log_level: str):
        """Manages thread pool for batch detection"""

        num_threads = int(os.cpu_count()/2) # Adjust based on your system (optimal for I/O bound tasks, less so for CPU bound)

        logger.info(f"\nExtracting texts with PaddleOCR in {num_threads} threads.")

        # Use ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all images for processing
            future_to_path = {executor.submit(self.run_paddleocr_on_detections, image, f"crop{number}_{i:02d}.png", detection, resizer, output_dir, log_level): detection for i, detection in enumerate(detections)}

            # Monitor progress and wait for all futures to complete
            for future in tqdm(concurrent.futures.as_completed(future_to_path), total=len(detections), desc="OCR"):
                image_path = future_to_path[future]
                try:
                    result = future.result()
                    if result:
                        all_results.append(result)
                except Exception as exc:
                    logger.error(f'{image_path} generated an exception: {exc}')

        # Return the populated, thread-safe results dictionary
        filtered_results = [result for result in all_results if result["original_text"] != ""]

        logger.success(f"Extracted {len(filtered_results)} texts.\n")

        return filtered_results

class MangaOCRRecognition:
    """
    A class to handle text extraction using Manga OCR.
    """
    def __init__(self, use_cpu: bool):
        """
        Initializes the Manga OCR model.
        :param use_gpu: Whether to use CPU for inference.
        """
        logger.info(f"Initializing Manga OCR model...")

        self.mocr = MangaOcr(force_cpu=use_cpu)

        logger.info("Manga OCR model initialized.")

    def run_mangaocr_on_detections(self, image: object, crop_name: str, detection: dict, resizer: list[bool | int], output_dir: str, log_level: str):

        use_resizer, resize_width = resizer

        with lock:
            try:
                box = detection["box"]

                xmin = box[0][0]
                ymin = box[0][1]
                xmax = box[2][0]
                ymax = box[2][1]

                cropped_img_resized = crop_out_box_pil([xmin, ymin, xmax, ymax], image, [use_resizer, resize_width], output_dir, crop_name, log_level)

                text = self.mocr(cropped_img_resized)

                if text and text != "．．．":
                    detection["original_text"] = text.strip()

                    if log_level == "INFO" and text != "":
                        logger.info(f"{text}")

                    return detection
            except Exception as e:
                logger.error(f"Error processing image: {e}")


    def batch_threaded2(self, image: object, number: int, detections: list[dict], resizer: list[bool | int], output_dir: str, log_level: str):
        """Manages thread pool for batch detection"""

        num_threads = int(os.cpu_count()/2)

        logger.info(f"\nExtracting texts with Manga OCR in {num_threads} threads.")

        # Use ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all images for processing
            future_to_path = {executor.submit(self.run_mangaocr_on_detections, image, f"crop{number}_{i:02d}.png", detection, resizer, output_dir, log_level): detection for i, detection in enumerate(detections)}

            # Monitor progress and wait for all futures to complete
            for future in tqdm(concurrent.futures.as_completed(future_to_path), total=len(detections), desc="OCR"):
                image_path = future_to_path[future]
                try:
                    result = future.result()
                    if result:
                        all_results.append(result)
                except Exception as exc:
                    logger.error(f'{image_path} generated an exception: {exc}')

        # Return the populated, thread-safe results dictionary
        filtered_results = [result for result in all_results if result["original_text"] != ""]

        # for rec in filtered_results:
        #     logger.info(f"{rec}\n")

        logger.success(f"Extracted {len(filtered_results)} texts.\n")

        return filtered_results