import os
import re
import sys
import time
import argparse
from PIL import Image
from tqdm import tqdm
from pathlib import Path
from loguru import logger
from datetime import datetime
from natsort import natsorted
from collections import Counter
from colorama import Fore, Back, Style, init

from _version import __version__
from app.core.config import load_config
from app.core.model import download_repo_snapshot
from app.core.image_utils import merge_images_vertically, slice_image_in_tiles_pil, split_image_safely
from app.core.detection import TextAreaDetection, merge_nearby_boxes
from app.core.ocr import PaddleOCRRecognition, MangaOCRRecognition
from app.core.translation import translate_texts_with_gemini
from app.core.overlay import overlay_translated_texts

# Measure time
start_time = time.perf_counter()

# Set other environment variables and configurations
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True" # not working :(
# os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = str(pow(2, 40))
Image.MAX_IMAGE_PIXELS = None
init(autoreset=True)

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

# Show app version
logger.info(f"SCT version: {__version__}\n")

# Load configurations from config.json
config = load_config('config.json')
if config:
    # For merging images
    merge_images = config['IMAGE_MERGE']['enable']
    # For text-area detection
    det_conf_threshold = config['OCR']['confidence_threshold']
    det_merge_threshold = config['DETECTION']['merge_threshold']
    tile_height = config['DETECTION']['tile']['height']
    tile_width = config['DETECTION']['tile']['width']
    tile_overlap = config['DETECTION']['tile']['overlap']
    # For OCR
    source_language = config['OCR']['source_language']
    ocr_conf_threshold = config['OCR']['confidence_threshold']
    use_upscaler = config['OCR']['upscale']['enable']
    upscale_ratio = config['OCR']['upscale']['ratio']
    # For splitting image
    max_height = config['IMAGE_SPLIT']['max_height']
    # For translation
    target_language = config['TRANSLATION']['target_language']
    gemini_model = config['TRANSLATION']['gemini']['model']
    gemini_temp = config['TRANSLATION']['gemini']['temperature']
    gemini_top_p = config['TRANSLATION']['gemini']['top_p']
    gemini_max_out_tokens = config['TRANSLATION']['gemini']['max_output_tokens']
    # For overlay
    box_offset = config['OVERLAY']['box']['offset']
    box_padding = config['OVERLAY']['box']['padding']
    box_fill_color = config['OVERLAY']['box']['fill_color']
    box_outline_color = config['OVERLAY']['box']['outline_color']
    font_min = config['OVERLAY']['font']['min_size']
    font_max = config['OVERLAY']['font']['max_size']
    font_color = config['OVERLAY']['font']['color']
    font_path = config['OVERLAY']['font']['path']

# --- Main Execution ---
image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
lang_code_jp = ("japanese", "japan", "jpn", "jp", "ja")

# Check if input path exists
if not os.path.exists(args.input):
    raise Exception(Fore.RED + f"{args.input} does not exist!")

# Download detection model if not exist
repo_id="ogkalu/comic-text-and-bubble-detector"
file_name="detector.onnx"
model_path=f"./models/detection/{repo_id}"

if not os.path.exists(f"{model_path}/{file_name}"):
    download_repo_snapshot(repo_id=repo_id, local_dir=model_path)

# Initialize models
detector = TextAreaDetection(model_path="models/detection/ogkalu/comic-text-and-bubble-detector/detector.onnx", confidence_threshold=det_conf_threshold, use_gpu=args.gpu)
det_target_size = 640

if source_language in lang_code_jp:
    extractor = MangaOCRRecognition(use_cpu=True if args.gpu == False else True)
else:
    extractor = PaddleOCRRecognition(ocr_version='PP-OCRv5', language=source_language, confidence_threshold=ocr_conf_threshold, use_gpu=args.gpu)

# Define previous directory
previous_dir = None

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
        # Update previous directory
        previous_dir = output_dir
        continue

    # Filter for image files and sort files to ensure consistent merging order
    image_files = [os.path.join(dirpath, f) for f in natsorted(filenames) if f.lower().endswith(image_extensions)]

    if not image_files:
        logger.info(Fore.BLUE + f"- No image in '{dirpath}'. Skipping.")
        continue

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

        # --- Stage 2: Detect Text Areas with ogkalu/comic-text-and-bubble-detector.onnx
        tile_width = image_width if tile_width == "original" else tile_width

        tile_height = tile_width if tile_height == "tile_width" else tile_height

        tile_overlap = int(tile_height * tile_overlap)

        image_slices = slice_image_in_tiles_pil(
            [merged_image, image_width, image_height], tile_height, tile_width, det_target_size, tile_overlap, "", output_dir, log_level
        )

        # detections = detector.batch_threaded("", image_slices, target_sizes=[tile_height, tile_width], log_level=log_level, image_tiled=True)

        logger.info(f"\nDetecting text areas with ogkalu/comic-text-and-bubble-detector.onnx.")
        detections = []
        for i, slice in enumerate(tqdm(image_slices)):
            detection = detector.detect_text_areas("", i, slice, target_sizes=[det_target_size, det_target_size], log_level=log_level, image_tiled=True)
            if detection:
                detections.extend(detection)

        merged_detections = merge_nearby_boxes(detections, det_merge_threshold)

        # --- Stage 3: Extract Texts with Manga OCR/PaddleOCR
        if source_language in lang_code_jp:
            recognitions = extractor.batch_threaded2(merged_image, "", merged_detections, [use_upscaler, upscale_ratio], output_dir, log_level)
        else:
            recognitions = extractor.batch_threaded(merged_image, "", merged_detections, [use_upscaler, upscale_ratio], output_dir, log_level)

        # --- Stage 4: Split Image Safely on Non-Text Areas ---
        image_chunks, chunks_number = split_image_safely([merged_image, image_width, image_height], recognitions, max_height)
    else:
        image_chunks = []
        recognitions = []

        for n, image in enumerate(images):
            image_width, image_height = image.size
            image_name = f"image_{n:02d}"
            image_chunks.append({
                "image_name": image_name,
                "image": image
            })

            # --- Stage 1: Detect Text Areas ogkalu/comic-text-and-bubble-detector.onnx
            tile_width = image_width if tile_width == "original" else tile_width

            tile_height = tile_width if tile_height == "tile_width" else tile_height

            tile_overlap = int(tile_height * tile_overlap)

            if image_width == det_target_size and tile_width == det_target_size:
                logger.info(f"\nDetecting text areas with ogkalu/comic-text-and-bubble-detector.onnx.")
                detections = detector.detect_text_areas(image_name, n, image, target_sizes=[det_target_size, det_target_size], log_level=log_level, image_tiled=False)
            else:
                image_slices = slice_image_in_tiles_pil([image, image_width, image_height], tile_height, tile_width, det_target_size, tile_overlap, n, output_dir, log_level)

                # detections = detector.batch_threaded(image_name,image_slices, target_sizes=[tile_height, tile_width], log_level=log_level, batch=True)

                logger.info(f"\nDetecting text areas with ogkalu/comic-text-and-bubble-detector.onnx.")
                detections = []
                for i, slice in enumerate(tqdm(image_slices)):
                    detection = detector.detect_text_areas(image_name, i, slice, target_sizes=[det_target_size, det_target_size], log_level=log_level, image_tiled=True)
                    detections.extend(detection)

            if not detections:
                logger.warning(Fore.YELLOW + "NO DETECTION! Skipping...")
                continue

            merged_detections = merge_nearby_boxes(detections, det_merge_threshold)

            # --- Stage 2: Extract Texts with Manga OCR/PaddleOCR
            if source_language in lang_code_jp:
                recognition = extractor.batch_threaded2(image, n, merged_detections, [use_upscaler, upscale_ratio], output_dir, log_level)

                # recognition = []
                # for i, detection in enumerate(merged_detections):
                #     rec = extractor.run_mangaocr_on_detections(image, f"crop{n}_{i:02d}.png", detection, [use_upscaler, upscale_ratio], output_dir, log_level)
                #     if rec:
                #         recognition.append(rec)
            else:
                recognition = extractor.batch_threaded(image, n, merged_detections, [use_upscaler, upscale_ratio], output_dir, log_level)

            recognitions.extend(recognition)

    # --- Stage 5/3: Translate Extracted Text with Gemini ---
    translated_text_data = translate_texts_with_gemini(recognitions, target_language, [gemini_model, gemini_temp, gemini_top_p, gemini_max_out_tokens], previous_dir, output_dir, log_level)

    # --- Stage 6/4: Whiten Text Areas & Overlay Translated Texts to Split Images ---
    overlay_translated_texts(image_chunks, merge_images, translated_text_data, [box_offset, box_padding, box_fill_color, box_outline_color], [font_min, font_max, font_color, font_path], common_original_extension, [source_language, lang_code_jp], output_dir, log_level)

    # Update previous directory
    previous_dir = output_dir

logger.info(Style.BRIGHT + Fore.GREEN + f"\nAll translated images saved to '{output_path}'.")

# --- End of Execution ---
end_time = time.perf_counter()
elapsed_seconds = end_time - start_time
hours, remainder = divmod(int(elapsed_seconds), 3600)
minutes, seconds = divmod(remainder, 60)
logger.info(f"\nTime taken: {hours:02}:{minutes:02}:{seconds:02}")