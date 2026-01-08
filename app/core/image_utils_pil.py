import os
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from loguru import logger
from collections import Counter


def merge_images_vertically(images: list[object], output_dir: str, log_level: str):
    """
    Merges all images in each subfolder into a single image and saves it 
    in the corresponding output subfolder.
    """

    image_count = len(images)
    logger.info(f"\nMerging {image_count} images into one.")

    # Determine the dimensions for the combined image (vertical stacking)
    widths, heights = zip(*(i.size for i in images))
    most_common_width, count = Counter(widths).most_common(1)[0]
    total_height = sum(heights)

    # Create a new blank image
    new_img = Image.new('RGB', (most_common_width, total_height), (255, 255, 255)) # White background

    # Paste each image below the previous one
    x_offset = 0
    y_offset = 0
    for img in images:
        # Center the image horizontally if it's not the max width
        if img.width != most_common_width:
            aspect_ratio = most_common_width / img.width
            new_height = int((img.height * aspect_ratio))
            total_height -= (img.height - new_height) # adjust total height for cropping after resizing width, removing black area
            img = img.resize((most_common_width, new_height), Image.Resampling.LANCZOS)

        new_img.paste(img, (x_offset, y_offset))
        y_offset += img.height

        # Crop images
        newer_width = x_offset + img.width
        newer_height = total_height

        cropped_region = (x_offset, 0,
                            newer_width,
                            newer_height)

        final_image = new_img.crop(cropped_region)

    logger.info("All images merged.")

    # Save the merged image if debug mode is on
    if log_level == "TRACE":
        output_path = f"{output_dir}/debug"
        os.makedirs(output_path, exist_ok=True)
        save_path = f"{output_path}/merged_image.png"
        final_image.save(save_path, quality=100)

    return final_image


def slice_image_in_tiles(image: list[object|int], tile_height: int, tile_width: int, target_max_dim: int, overlap: int, number: int, output_dir:str, log_level:str) -> list[dict]:
    """
    Generates overlapping image tiles (sliding window) for OCR processing. 
    Resizes tiles to fit within target_max_dim while maintaining aspect ratio,
    and returns the scaling factors.
    """
    img_pil, width, height = image

    tiles = []

    stride_y = tile_height - overlap
    stride_x = tile_width - overlap
    if stride_y <= 0: stride_y = tile_height
    if stride_x <= 0: stride_x = tile_width

    for top in range(0, height, stride_y):
        for left in range(0, width, stride_x):
            effective_top = max(0, min(top, height - tile_height))
            effective_left = max(0, min(left, width - tile_width))
            box = (effective_left, effective_top, effective_left + tile_width, effective_top + tile_height)
            cropped_img_pil = img_pil.crop(box)

            # Resize image if its size is not equal to target dimension for the detection model (640x640)
            original_tile_w, original_tile_h = cropped_img_pil.size
            scale_x = 1
            scale_y = 1

            if original_tile_w != target_max_dim or original_tile_h != target_max_dim:
                cropped_img_pil = cropped_img_pil.resize((target_max_dim, target_max_dim), Image.Resampling.LANCZOS)

                # Calculate scaling factors
                resized_tile_w, resized_tile_h = cropped_img_pil.size
                scale_x = original_tile_w / resized_tile_w
                scale_y = original_tile_h / resized_tile_h

            tiles.append({
                'image': cropped_img_pil, 
                'top_offset': effective_top, 
                # 'bottom_offset': effective_top + tile_height, 
                'left_offset': effective_left,
                # 'right_offset': effective_left + tile_width,
                'scale_x': scale_x,
                'scale_y': scale_y
            })
            if left + tile_width >= width: break
        if top + tile_height >= height: break

    # Save image tiles if debug mode is on
    if log_level == "TRACE":
        output_path = f"{output_dir}/debug/tile"
        os.makedirs(output_path, exist_ok=True)
        for i, slice in enumerate(tiles):
            image_slice = slice["image"]
            save_path = f"{output_path}/tile{number}_{i:02d}.png"
            image_slice.save(save_path, quality=100)

    return tiles

def crop_out_box(box: list[int], image: object, upscale: list[bool|int|float], output_dir: str, crop_name: str, log_level: str) -> object:
    [xmin, ymin, xmax, ymax] = box
    use_upscaler, upscale_ratio = upscale

    # Ensure coordinates are valid for cropping
    xmin, ymin, xmax, ymax = max(0, xmin), max(0, ymin), min(image.size[0], xmax), min(image.size[1], ymax)

    # Crop the detection from the original image
    cropped_img = image.crop((xmin, ymin, xmax, ymax))

    # --- Resizing while maintaining aspect ratio for OCR input ---
    w, h = cropped_img.size

    # Upscale cropped image if enabled
    if use_upscaler:
        new_w = int(w * upscale_ratio)
        new_h = int(h * upscale_ratio)

        cropped_img = cropped_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if log_level == "TRACE":
        save_path = f"{output_dir}/debug/crop"
        os.makedirs(save_path, exist_ok=True)
        cropped_img.save(f"{save_path}/{crop_name}", quality=100)

    return cropped_img


def split_image_safely(image: list[object|int], detections: list[dict], max_height: int) -> tuple[list, range]:
    """
    Split image on non-text areas, avoiding bounding boxes, within the specified maximum height.
    """
    logger.info("\nSplitting image on non-text areas.")

    img, width, height = image
    split_points = [0]
    current_pos = 0
    offset = 20

    boxes8 = [boxes["box"] for boxes in detections]

    while current_pos < height:
        # Determine the maximum possible safe height for the current chunk
        max_safe_y = min(current_pos + max_height, height)

        # Look for a safe split point within the allowed range (e.g., in a margin)
        # For simplicity here, we look for a y-coordinate that doesn't intersect any bubble

        best_split = max_safe_y

        # Iterate backwards from max_safe_y to find a safe boundary
        for y in range(max_safe_y, current_pos, -1):
            is_safe = True
            for box in boxes8:
                y_min, y_max = box[0][1]-offset, box[2][1]+offset
                if y > y_min and y < y_max:
                    is_safe = False
                    break
            if is_safe:
                best_split = y
                break

        # If no perfectly safe spot is found within the range, you might have to adjust your logic
        # (e.g., split at the edge of the nearest bubble, or use a panel detection model first)
        # Assuming there are sufficient white spaces between bubbles for splits:

        split_points.append(best_split)
        current_pos = best_split

        if current_pos >= height:
            break

    # Perform the actual splitting
    chunks = []
    for i in range(len(split_points) - 1):
        y_start = split_points[i]
        y_end = split_points[i + 1]
        if y_end > y_start:
            chunk = img.crop((0, y_start, width, y_end))
            chunks.append({
                "image": chunk,
                "top_offset": y_start,
            })

    chunks_total = len(chunks)
    chunks_number = range(chunks_total)
    logger.info(f"Image splitted into {chunks_total} parts.")

    return chunks, chunks_number