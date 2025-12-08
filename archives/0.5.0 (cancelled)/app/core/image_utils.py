import os
from PIL import Image
from loguru import logger
Image.MAX_IMAGE_PIXELS = None
from collections import Counter


def merge_images_vertically(images, output_dir, log_level):
    """
    Merges all images in each subfolder into a single image and saves it 
    in the corresponding output subfolder.
    """

    image_count = len(images)
    logger.info(f"Merging {image_count} images into one.")

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

    logger.info("All images merged.\n")

    # Save the merged image if debug mode is on
    if log_level == "TRACE":
        output_path = f"{output_dir}/debug"
        os.makedirs(output_path, exist_ok=True)
        save_path = f"{output_path}/merged_image.png"
        final_image.save(save_path, quality=100)
        logger.debug(f"Merged {len(images)} images and saved to {save_path}.")

    return final_image


def slice_image_in_tiles(image_path, tile_height, tile_width, overlap, output_dir, log_level):
    """
    Generates overlapping image tiles (sliding window) using Pillow for cropping.
    Returns a list of tile information dictionaries with PIL Image objects.
    """
    image, width, height = image_path
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
            cropped_img_pil = image.crop(box)
            
            tiles.append({
                'image': cropped_img_pil,
                'top_offset': effective_top, 
                'bottom_offset': effective_top + tile_height, 
                'left_offset': effective_left,
                'right_offset': effective_left + tile_width
            })
            
            if left + tile_width >= width: break
        if top + tile_height >= height: break

    # Save image tiles if debug mode is on
    if log_level == "TRACE":
        output_path = f"{output_dir}/debug"
        os.makedirs(output_path, exist_ok=True)
        for i, slice in enumerate(tiles):
            image_slice = slice["image"]
            save_path = f"{output_path}/tile_{i:02d}.png"
            image_slice.save(save_path, quality=100)
            image_slice.close
            logger.debug(f"Saved {len(tiles)} image tiles to {save_path}.")

    return tiles


def split_image_safely(image, detection, max_height=10000):
    """
    Split image on non-text areas.
    """
    img, width, height = image
    split_points = [0]
    current_pos = 0
    offset = 20

    boxes8 = [boxes["box"] for boxes in detection]

    logger.info("\nSplitting image on non-text areas.")
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
            chunks.append(
                {
                    "image": chunk,
                    "top_offset": y_start,
                }
            )
            # chunk.save(f"output_chunk_{i+1}.png")

    chunks_total = len(chunks)
    chunks_number = range(chunks_total)
    logger.info(f"Image splitted into {chunks_total} parts.\n")

    return chunks, chunks_number