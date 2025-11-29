# -*- coding: utf-8 -*- 

import os
import re
import time
import logging
import argparse
from PIL import Image
from pathlib import Path
from natsort import natsorted
from collections import Counter
from colorama import Fore, Back, Style, init

from app.core.config import load_config
from app.core.model import download_repo_snapshot
from app.core.image_utils import merge_images_vertically, split_image_safely
from app.core.detection import detect_text_areas
from app.core.ocr import process_region_with_ocr, merge_nearby_boxes
from app.core.translation import translate_texts_with_gemini
from app.core.overlay import overlay_translated_texts

# Set the environment variables
Image.MAX_IMAGE_PIXELS = None
logging.basicConfig(level=logging.INFO)

start_time = time.perf_counter()

init(autoreset=True)

# Define arguments with argparse
parser = argparse.ArgumentParser(description="Arguments for Simple Comic Translator.")
parser.add_argument("--input", type=str, help="Path to a folder containing comic")
parser.add_argument("--output", type=str, help="Path to output folder to save translated comic")
parser.add_argument("--gpu", type=bool, default=False, help="Using GPU or not")

args = parser.parse_args()

INPUT_PATH = args.input
output_path = args.output if args.output else f"{INPUT_PATH}-translated"

# Read configurations from config.json
# Load the configuration
config = load_config('config.json')

# Access configuration values
if config:
    # For merging images
    image_merge = config['IMAGE_MERGE']['enable']
    # For text-area detection
    slice_height = config['DETECTION']['slice_height']
    export_visuals = config['DETECTION']['export_visuals']
    # For splitting image
    max_height = config['IMAGE_SPLIT']['max_height']
    # For OCR
    ocr_language = config['OCR']['language']
    ocr_slice = config['OCR']['use_slice']
    merge_y_threshold = config['OCR']['merge_y_threshold'] # Max vertical distance in pixels to consider for merging
    # For translation
    target_language = config['TRANSLATION']['target_language']
    gemini_model = config['TRANSLATION']['gemini_model']
    # For overlay
    font_size = config['OVERLAY']['font_size']
    font_path = config['OVERLAY']['font_path']

# --- Main Execution ---

image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')

# Check if input path exists
if not os.path.exists(args.input):
    raise Exception(Fore.RED + f"{args.input} does not exist!")

# Download models if not exist
repo_id="ogkalu/comic-speech-bubble-detector-yolov8m"
file_name="comic-speech-bubble-detector.pt"
model_path=f"./models/detection/{repo_id}"

if not os.path.exists(f"{model_path}/repo"):
    download_repo_snapshot(
        repo_id=repo_id,
        local_dir=f"{model_path}/repo"
    )

# Iterate through all directories using os.walk
for dirpath, dirnames, filenames in natsorted(os.walk(args.input)):

    # Define the output path
    relative_path = Path(dirpath).relative_to(args.input)
    output_dir = Path(output_path) / relative_path
    output_dir.mkdir(parents=True, exist_ok=True) # Create output directory if it doesn't exist

    print(Style.BRIGHT + Fore.YELLOW + f"\nProcessing '{dirpath}'")

    # Skip if output files already exist
    already_exist = False
    regex_pattern = r"^image_.*"

    for filename in os.listdir(output_dir):
        full_path = os.path.join(output_dir, filename)

        if re.match(regex_pattern, filename):
            if os.path.exists(full_path):
                print(Fore.GREEN + f"- Files already exist in '{output_dir}'. Skipping.")
                already_exist = True
                break

    if already_exist:
        continue

    # Filter for image files (you can add more extensions if needed)
    image_files = [os.path.join(dirpath, f) for f in filenames if f.lower().endswith(image_extensions)]

    if not image_files:
        print(Fore.BLUE + f"- No image in '{dirpath}'. Skipping.")
        continue

    # Sort files to ensure consistent merging order
    natsorted(image_files)

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

    # --- Stage 1: Merge images into one ---
    merged_image = merge_images_vertically(images)

    image_width, image_height = merged_image.size

    # --- Stage 2: Detect Text Areas with ogkalu/comic-speech-bubble-detector-yolov8m + SAHI ---
    detection = detect_text_areas(merged_image, image_width, slice_height, export_visuals, output_dir, args.gpu)

    # --- Stage 3: Split Image Safely on Non-Text Areas ---
    image_chunks, chunks_number = split_image_safely(merged_image, image_width, image_height, detection, max_height)

    # --- Stage 4: Extract Text with PaddleOCR ---
    ocr_results = process_region_with_ocr(image_chunks, ocr_language, ocr_slice, args.gpu)

    # --- Stage 5: Merge Nearby Boxes from OCR Results ---
    merged_text_data = (merge_nearby_boxes(ocr_results, merge_y_threshold, chunks_number))

    # --- Stage 6: Translate Extracted Text with Gemini ---
    translated_text_data = translate_texts_with_gemini(
    merged_text_data, target_language, gemini_model)

    # --- Stage 7: Whiten/Inpaint Text Areas & Overlay Translated Text to Split Images ---
    overlay_translated_texts(translated_text_data, font_size, font_path, image_chunks, output_dir, common_original_extension)

print(Style.BRIGHT + Fore.GREEN + f"\nAll translated images saved to '{output_path}'.")

# --- End of Execution ---
end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(f"Time taken: {elapsed_time:.2f} seconds")