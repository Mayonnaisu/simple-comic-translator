import os
import textwrap
import numpy as np
from loguru import logger
from colorama import Fore, Style, init
from PIL import Image, ImageDraw, ImageFont

from app.core.detection import get_bbox_coords
from app.core.inpainting import inpaint_image_with_lama

init(autoreset=True)

# def is_string_in_file(file_path: int, search_string: str):
#     with open(file_path, 'r', encoding="utf-8") as file:
#         for line in file:
#             if search_string in line:
#                 return True
#     return False


def get_fitted_font_and_text(text: str, max_width: int, max_height: int, min_size: int, max_size: int, font_path: int):
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
        wrapped_text_list = textwrap.wrap(text, width=chars_per_line if chars_per_line > 0 else 1)
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


def overlay_translated_texts(images: list[dict], images_merged: bool, all_ocr_results: list[dict], box: list[int | str | tuple], inpainting: list[bool|object], font: list[int | str], image_extension: str, source_language: str, output_path: str, log_level: str):
    """Overlays the detected text boxes and translated texts onto the corresponding safely-splitted images and saves them."""

    logger.info("\nOverlaying translated texts.")

    if not os.path.exists(output_path): os.makedirs(output_path)

    box_offset, box_padding, box_fill_color, box_outline_color, box_outline_thickness = box
    inpaint, inpainter = inpainting
    font_min, font_max, font_color, font_path = font

    # inclusion = ("i", "you", "we", "they", "he", "she", "it", "ah")

    # # Set filter according to source source_language
    # source_language, lang_code_jp = source_language

    # if source_language in lang_code_jp:
    #     filter_path = "filters/manga.txt"
    # elif source_language == "korean":
    #     filter_path = "filters/manhwa.txt"
    # elif source_language == "ch":
    #     filter_path = "filters/manhua.txt"

    for i, image_info in enumerate(images):
        image_name = f"image_{i:02d}"

        if images_merged:
            image_slice = image_info['image'].copy()
            slice_top = image_info['top_offset']
            image = image_slice

            results_for_this_slice = []
            for res in all_ocr_results:
                s_min_y, s_max_y = np.min(np.array(res['box'])[:, 1]), np.max(np.array(res['box'])[:, 1])
                if max(slice_top, s_min_y) < min(slice_top + image_slice.size[1], s_max_y):
                     results_for_this_slice.append(res)
        else:
            image = image_info['image'].copy()
            image_name = image_info['image_name']
            slice_top = 0

            results_for_this_slice = []
            for res in all_ocr_results:
                if res["image_name"] == image_name:
                    results_for_this_slice.append(res)

        draw = ImageDraw.Draw(image)

        for item in results_for_this_slice:
            original_points = item["box"]
            original_text = item["original_text"]
            # Filter out sound effects and watermarks
            translated_text = item["translated_text"].replace("(redacted)", "")

            if translated_text == "" or translated_text == " ":
                continue

            # Filter out sound effects in original_text
            # if is_string_in_file(filter_path, original_text):
            #     continue

            # Filter out translated texts whose characters are fewer than 3 and not in inclusion list, potentially removing gibberish
            # if len(translated_text) < 3 and translated_text.lower() not in inclusion:
            #     continue

            # Adjust points back to be relative to the *current split's* top edge
            relative_points = [[p[0], p[1] - slice_top] for p in original_points]

            # Add offsets to enlarge text areas
            rel_xmin, rel_ymin, rel_xmax, rel_ymax, _ = get_bbox_coords(relative_points)

            new_xmin = rel_xmin - box_offset
            new_ymin = rel_ymin - box_offset
            new_xmax = rel_xmax + box_offset
            new_ymax = rel_ymax + box_offset

            box_width = new_xmax - new_xmin
            box_height = new_ymax - new_ymin

            # Use textwrap as a safety measure to prevent spilling
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
            target_box_x1, target_box_y1 = (new_xmin, new_ymin)
            target_box_center_x = target_box_x1 + box_width // 2
            target_box_center_y = target_box_y1 + box_height // 2

            text_x = target_box_center_x - text_width // 2
            text_y = target_box_center_y - text_height // 2

            # Inpaint or overlay the target bounding box
            if inpaint:
                image = inpaint_image_with_lama(inpainter, image, [rel_xmin, rel_ymin, rel_xmax, rel_ymax],output_path, i, log_level)

                draw = ImageDraw.Draw(image)
            else:
                draw.rectangle(
                    (target_box_x1, target_box_y1, target_box_x1 + box_width, target_box_y1 + box_height),
                    fill=box_fill_color,
                    outline=box_outline_color,
                    width=box_outline_thickness
                )

            # Draw the text
            text_position = (text_x, text_y-box_padding)
            draw.multiline_text(
                text_position,
                wrapped_text,
                align="center",
                font=final_font,
                fill=font_color
            )

            # Annotate image in debug mode
            if log_level == "TRACE":
                annotate = ImageDraw.Draw(image_info['image'])

                try:
                    font = ImageFont.truetype(font_path, 30)
                except IOError:
                    font = ImageFont.load_default()

                annotate.rectangle(
                    (rel_xmin, rel_ymin, rel_xmax, rel_ymax),
                    outline="red",
                    width=2
                )
                annotate.text(
                    (rel_xmin, rel_ymin - 35),
                    original_text,
                    font=font,
                    fill="green",
                )

        # Save the final image
        full_output_path = f"{output_path}/{image_name}.{image_extension}"
        image.save(full_output_path, quality=100)
        image.close()

        # Save the annotated image in debug mode
        if log_level == "TRACE":
            full_output_path = f'{output_path}/debug/annotation'
            os.makedirs(full_output_path, exist_ok=True)
            annotation_image = image_info['image']
            annotation_name = f"annotated_{i:02d}.jpg"
            annotation_image.save(f'{full_output_path}/{annotation_name}', quality=100)
            logger.success(f"Saved {annotation_name}.")
            annotation_image.close()

    logger.success("Translated texts overlaid.")
    logger.success(Fore.GREEN + f"\nTranslated images saved to {output_path}.")