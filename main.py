# -*- coding: utf-8 -*- 

import os
import re
import sys
import time
import argparse
import itertools
from PIL import Image
from pathlib import Path
from loguru import logger
from datetime import datetime, timedelta
from natsort import natsorted
from collections import Counter
from colorama import Fore, Back, Style, init

from app.core.config import load_config
from app.core.image_utils import merge_images_vertically, slice_image_horizontally, split_image_safely
from app.core.ocr import run_ocr_on_slices, deduplicate_results, merge_nearby_boxes
from app.core.translation import translate_texts_with_gemini
from app.core.overlay import overlay_translated_texts

# Measure time
start_time = time.perf_counter()

# Set the environment variables and configurations
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = str(pow(2, 40))
Image.MAX_IMAGE_PIXELS = None
init(autoreset=True, convert=True)

# Define arguments with argparse
parser = argparse.ArgumentParser(description="Arguments for Simple Comic Translator.")
parser.add_argument("--input", type=str, help="(str): path to your comic folder")
parser.add_argument("--output", type=str, help="(str): path to output folder")
parser.add_argument("--gpu", action='store_true', help="use GPU")
parser.add_argument("--debug", action='store_true', help="enable debug mode")

args = parser.parse_args()

input_path = args.input
output_path = args.output if args.output else f"{input_path}-shitted"

# Start logging
logger.remove() # Remove the default handler

log_level = "INFO" if args.debug == False else "TRACE"
formatted_datetime = datetime.now().strftime("%Y-%m-%d_%H.%M")

logger.add(sys.stderr, format="{message}", level=log_level)
logger.add(f"temp/logs/{formatted_datetime}.log", format="{message}", level=log_level)

# Read configurations from config.json
# Load the configuration
config = load_config('config.json')

# Access configuration values
if config:
    # For merging images
    merge_images = config['IMAGE_MERGE']['enable']
    # For text-area detection
    source_language = config['DETECTION']['source_language']
    slice_height = config['DETECTION']['slice_height']
    ocr_overlap = int(slice_height * config['DETECTION']['ocr_overlap'])
    det_y_threshold = config['DETECTION']['merge_y_threshold']
    det_x_threshold = config['DETECTION']['merge_x_threshold'] 
    # For splitting image
    max_height = config['IMAGE_SPLIT']['max_height']
    # For OCR
    ocr_y_threshold = config['OCR']['merge_y_threshold']
    ocr_x_threshold = config['OCR']['merge_x_threshold']
    use_slicer = config['OCR']['slicer']['enable']
    h_stride = config['OCR']['slicer']['horizontal_stride']
    v_stride = config['OCR']['slicer']['vertical_stride']
    # For translation
    target_language = config['TRANSLATION']['target_language']
    gemini_model = config['TRANSLATION']['gemini_model']
    # For overlay
    font_min = config['OVERLAY']['font']['min_size']
    font_max = config['OVERLAY']['font']['max_size']
    font_path = config['OVERLAY']['font']['path']

# --- Main Execution ---
image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')

# Check if input path exists
if not os.path.exists(args.input):
    raise Exception(Fore.RED + f"{args.input} does not exist!")

# Iterate through all directories using os.walk
for dirpath, dirnames, filenames in natsorted(os.walk(args.input)):

    # Define the output path
    relative_path = Path(dirpath).relative_to(args.input)
    output_dir = Path(output_path) / relative_path
    output_dir.mkdir(parents=True, exist_ok=True) # Create output directory if it doesn't exist

    logger.info(Style.BRIGHT + Fore.YELLOW + f"\nProcessing '{dirpath}'")

    # Skip if output files already exist
    already_exist = False
    regex_pattern = r"^image_.*"

    for filename in os.listdir(output_dir):
        full_path = os.path.join(output_dir, filename)

        if re.match(regex_pattern, filename):
            if os.path.exists(full_path):
                logger.info(Fore.GREEN + f"- Files already exist in '{output_dir}'. Skipping.")
                already_exist = True
                break

    if already_exist:
        continue

    # Filter for image files (you can add more extensions if needed)
    image_files = [os.path.join(dirpath, f) for f in filenames if f.lower().endswith(image_extensions)]

    if not image_files:
        logger.info(Fore.BLUE + f"- No image in '{dirpath}'. Skipping.")
        continue

    # Sort files to ensure consistent merging order
    image_files = natsorted(image_files)

    images = []
    try:
        for file in image_files:
            img = Image.open(file)
            images.append(img)
    except IOError as e:
        raise Exception(Fore.RED + f"Error opening image {file}: {e}")

    if not images:
        continue

    # Get the most common original extension
    original_extensions = []
    for file in image_files:
        original_extension = file.split('.')[-1].lower()
        original_extensions.append(original_extension)
        original_extension_counts = Counter(original_extensions)
        common_original_extension, counts = original_extension_counts.most_common(1)[0]


    if merge_images:
        # --- Stage 1: Merge images into one ---
        merged_image = merge_images_vertically(images, output_dir, log_level)

        image_width, image_height = merged_image.size

        # --- Stage 2: Detect Text Areas PaddleOCR
        image_slices = slice_image_horizontally(
            [merged_image, image_width, image_height], slice_height, ocr_overlap, output_dir, log_level
        )
        detections = run_ocr_on_slices(image_slices, source_language, args.gpu, [use_slicer, h_stride, v_stride], process="detection")

        unique_detections = deduplicate_results(detections, iou_threshold=0.6)

        merged_detections = merge_nearby_boxes(unique_detections, det_y_threshold, det_x_threshold, process="detection")

        # --- Stage 3: Split Image Safely on Non-Text Areas ---
        image_chunks, chunks_number = split_image_safely([merged_image, image_width, image_height], merged_detections, max_height)
    else:
        image_chunks = images
        chunks_number = range(len(image_chunks))

    # --- Stage 4: Extract Text with PaddleOCR ---
    ocr_results = run_ocr_on_slices(image_chunks, source_language, args.gpu, [use_slicer, h_stride, v_stride], process="ocr")

    merged_ocr = []
    for i in chunks_number:
        detected_items = []
        chunk_name = f"image_{i:02d}"
        for item in ocr_results:
            if item["image_name"] == chunk_name:
                detected_items.append(item)

        merged_ocr.append(merge_nearby_boxes(detected_items, ocr_y_threshold, ocr_x_threshold, process="ocr"))

    merged_ocr_results = list(itertools.chain.from_iterable(merged_ocr))

    # --- Stage 5: Translate Extracted Text with Gemini ---
    translated_text_data = translate_texts_with_gemini(merged_ocr_results, target_language, gemini_model, output_dir)

    # --- Stage 6: Whiten Text Areas & Overlay Translated Texts to Split Images ---
    overlay_translated_texts(image_chunks, translated_text_data, [font_min, font_max, font_path], common_original_extension, source_language, output_dir)

logger.info(Style.BRIGHT + Fore.GREEN + f"\nAll translated images saved to '{output_path}'.")

# --- End of Execution ---
end_time = time.perf_counter()
elapsed_seconds = end_time - start_time
hours, remainder = divmod(int(elapsed_seconds), 3600)
minutes, seconds = divmod(remainder, 60)
logger.info(f"\nTime taken: {hours:02}:{minutes:02}:{seconds:02}")