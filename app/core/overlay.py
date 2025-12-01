import os
import textwrap
import numpy as np
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
            print(f"Font file {font_path} not found. Using default font.")
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

def overlay_translated_texts(non_overlap_slices, all_ocr_results, font, image_extension, language, output_path):
    """Maps OCR results to the correct non-overlapping slice and draws them."""
    font_min, font_max, font_path = font

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    inclusion = ("I", "you", "we", "they", "he", "she", "it")

    # Set filter according to source language
    if language == "japan":
        filter_path = "filters/manga.txt"
    elif language == "korean":
        filter_path = "filters/manhwa.txt"
    elif language == "ch":
        filter_path = "filters/manhua.txt"

    for i, slice_info in enumerate(non_overlap_slices):
        slice_name = f"image_{i:02d}"
        try:
            slice_img_pil = slice_info["image"]
        except Exception:
            slice_img_pil = slice_info

        draw = ImageDraw.Draw(slice_img_pil)

        for item in all_ocr_results:
            if item["image_name"] == slice_name:
                box = item["box"]
                original_text = item["original_text"]
                translated_text = item["translated_text"]

                # Filter for sound effects in original_text
                if is_string_in_file(filter_path, original_text):
                    continue
                # Filter translated texts whose characters are fewer than 4 and not in inclusion list, potentially removing gibberish
                if len(translated_text) < 4 and translated_text not in inclusion:
                    continue
                # Adjust points back to be relative to the *current slice's* top edge
                rel_min_x, rel_min_y, rel_max_x, rel_max_y, _ = get_bbox_coords(
                    [[p[0], p[1]] for p in box]
                )

                offset = 10
                new_y_min = rel_min_y - offset
                new_y_max = rel_max_y + offset
                new_x_min = rel_min_x - offset
                new_x_max = rel_max_x + offset

                box_width = new_x_max - new_x_min
                box_height = new_y_max - new_y_min

                # Use textwrap on the *already structured* text from Gemini
                # This acts as a secondary safety measure to prevent spilling
                optimal_size, wrapped_text = get_fitted_font_and_text(
                    translated_text, box_width, box_height, font_min, font_max, font_path
                )

                final_font = ImageFont.truetype(font_path, optimal_size)

                # Calculate position to center the text within the target box
                bbox = draw.multiline_textbbox(
                    (0, 0), wrapped_text, font=final_font, align="center"
                )
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Center the text within the target box region
                target_box_x1, target_box_y1 = (new_x_min, new_y_min)
                target_box_center_x = target_box_x1 + box_width // 2
                target_box_center_y = target_box_y1 + box_height // 2

                text_x = target_box_center_x - text_width // 2
                text_y = target_box_center_y - text_height // 2

                # Optional: Draw the target bounding box or inpaint the original text (TODO)
                draw.rectangle(
                    (target_box_x1, target_box_y1, target_box_x1 + box_width, target_box_y1 + box_height),
                    fill="white",
                    # outline="red"
                )

                # Draw the text
                text_position = (text_x, text_y)
                draw.multiline_text(
                    text_position,
                    wrapped_text,
                    align="center",
                    font=final_font,
                    fill="black",
                )

        # Save the processed slice image
        # os.makedirs(output_path, exist_ok=True)
        full_output_path = f"{output_path}/{slice_name}.{image_extension}"
        slice_img_pil.save(full_output_path, quality=100)
        slice_img_pil.close()

    print(f"Translated images saved to {output_path}.")