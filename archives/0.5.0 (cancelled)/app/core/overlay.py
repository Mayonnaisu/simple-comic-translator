import os
import textwrap
import numpy as np
from loguru import logger
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont

from app.core.ocr import get_bbox_coords


def is_string_in_file(file_path, search_string):
    with open(file_path, 'r', encoding="utf-8") as file:
        for line in file:
            if search_string in line:
                return True
    return False


def get_fitted_font_and_text(text, max_width, max_height, min_size, max_size, font_path):
    """
    Finds the largest font size and the corresponding wrapped text that fits within the specified max_width and max_height.
    """
    fitted_size = min_size
    best_wrapped_text = ""

    for size in range(max_size, min_size, -1):
        try:
            font = ImageFont.truetype(font_path, size)
        except IOError:
            logger.info(f"Font file {font_path} not found. Using default font.")
            font = ImageFont.load_default()

        # Determine how many characters per line are needed for this font size
        # This is an approximation; a more complex approach might be needed
        # for highly variable-width fonts.
        avg_char_width = font.getbbox("a")[2] - font.getbbox("a")[0]
        if avg_char_width == 0:
            continue  # Avoid division by zero
        chars_per_line = int(max_width / avg_char_width) if avg_char_width > 0 else 1

        # Wrap text based on calculated characters per line
        wrapped_text_list = textwrap.wrap(text, width=chars_per_line)
        wrapped_text = "\n".join(wrapped_text_list)

        # Measure the total size of the wrapped text using ImageDraw.multiline_textbbox
        # We need a dummy draw object for this measurement
        dummy_image = Image.new("RGB", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_image)
        bbox = dummy_draw.multiline_textbbox(
            (0, 0), wrapped_text, font=font, align="center"
        )

        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        fitted_size = size
        best_wrapped_text = wrapped_text

        if width < max_width and height < max_height:
            break

    # Return the last size and text that fit
    return fitted_size, best_wrapped_text


def overlay_translated_texts(tiles: List[Dict], all_ocr_results: List[Dict], output_folder: str):
    """Overlays the detected text boxes onto the corresponding non-overlapping tiles and saves them."""
    if not os.path.exists(output_folder): os.makedirs(output_folder)

    for i, tile_info in enumerate(tiles):
        slice_top = tile_info['top_offset']
        slice_img_pil = tile_info['image'].copy() 
        draw = ImageDraw.Draw(slice_img_pil)
        
        results_for_this_slice = []
        for res in all_ocr_results:
            s_min_y, s_max_y = np.min(np.array(res['box'])[:, 1]), np.max(np.array(res['box'])[:, 1])
            if max(slice_top, s_min_y) < min(slice_top + slice_img_pil.size[1], s_max_y):
                 results_for_this_slice.append(res)
        
        try:
            font = ImageFont.truetype("fonts/NotoSerifKR-Regular.ttf", 30)
        except IOError:
            font = ImageFont.load_default()

        for item in results_for_this_slice:
            original_points = item['box']
            text = item["original_text"]
            # Adjust points back to be relative to the *current tile's* top edge
            relative_points = [[p[0], p[1] - slice_top] for p in original_points]
            xmin, ymin, xmax, ymax, _ = get_bbox_coords(relative_points)
            draw.rectangle((xmin, ymin, xmax, ymax), outline="red", width=2)
            draw.text(
                (relative_points[0][0], relative_points[0][1] - 35),
                text,
                font=font,
                fill="green",
            )

        output_path = os.path.join(output_folder, f'tile_aligned_{i+1:02d}.jpg')
        slice_img_pil.save(output_path, quality=100)
        slice_img_pil.close
        print(f"Saved aligned tile to {output_path} (Y offset: {slice_top})")
