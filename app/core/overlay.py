import os
import numpy as np
from PIL import ImageDraw, ImageFont
import textwrap


def overlay_translated_texts(text_info_list, font_size, font_path, image_path, output_path, extension):
    padding = 5

    try:
        font = ImageFont.truetype(font_path, size=font_size)
    except IOError:
        print(f"Font file {font_path} not found. Using default font.")
        font = ImageFont.load_default()

    for i, chunk in enumerate(image_path):
        name = f"image_{str(i).zfill(2)}"
        img_pil = chunk
        draw = ImageDraw.Draw(img_pil)
        for info in text_info_list:
            if info["image_name"] == name:
                box = info["box"]
                translated_text = info["translated_text"]
    
                x_coords = box[:, 0]
                y_coords = box[:, 1]
                x_min, x_max = int(np.min(x_coords)), int(np.max(x_coords))
                y_min, y_max = int(np.min(y_coords)), int(np.max(y_coords))
    
                box_width = (x_max + padding) - (x_min - padding*15)
        
                avg_char_width = font.getlength("a")
                if avg_char_width == 0:
                    max_chars_per_line = int(box_width / 10)
                else:
                    max_chars_per_line = int((box_width - 2 * padding) / avg_char_width)
        
                # Use textwrap on the *already structured* text from Gemini
                # This acts as a secondary safety measure to prevent spilling
                wrapped_lines = textwrap.wrap(
                    translated_text, width=max_chars_per_line or box_width
                )
                fitted_text = "\n".join(wrapped_lines)
    
                offset = 20
                new_y_min = y_min - offset
                new_y_max = y_max + offset
                new_x_min = x_min - offset
                new_x_max = x_max + offset
        
                draw.rectangle(
                    [new_x_min, new_y_min, new_x_max, new_y_max], fill=(255, 255, 255)
                )
    
                text_position = (new_x_min + padding, new_y_min + padding)
                draw.multiline_text(text_position, fitted_text, align="center", font=font, fill=(0, 0, 0))
    
        os.makedirs(output_path, exist_ok=True)
        full_output_path = f"{output_path}/{name}.{extension}"
        img_pil.save(full_output_path, quality=100)

    print(f"Translated images saved to {output_path}")