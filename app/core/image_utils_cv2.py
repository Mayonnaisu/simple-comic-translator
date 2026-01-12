import os
import cv2
import numpy as np
from loguru import logger
from collections import Counter


def merge_images_vertically(images, output_dir, log_level):
    """
    Merges all images in a folder vertically into a single image using OpenCV.
    'images' is expected to be a list of numpy arrays (OpenCV images).
    """
    image_count = len(images)
    logger.info(f"\nMerging {image_count} images into one.")

    # In OpenCV, size is accessed via img.shape -> (height, width, channels)
    widths = [img.shape[1] for img in images]
    most_common_width, _ = Counter(widths).most_common(1)[0]

    processed_images = []
    total_height = 0

    for img in images:
        h, w = img.shape[:2]
        
        # Resize if width doesn't match most common width
        if w != most_common_width:
            aspect_ratio = most_common_width / w
            new_height = int(h * aspect_ratio)
            # Use INTER_LANCZOS4 for high-quality downsampling (equivalent to LANCZOS)
            img = cv2.resize(img, (most_common_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            h, w = img.shape[:2]
        
        processed_images.append(img)
        total_height += h

    # Create a new blank white image (height, width, 3 channels)
    # Using uint8 for standard 8-bit images
    final_image = np.full((total_height, most_common_width, 3), 255, dtype=np.uint8)

    # "Paste" images by assigning them to array slices
    current_y = 0
    for img in processed_images:
        h, w = img.shape[:2]
        final_image[current_y : current_y + h, 0 : w] = img
        current_y += h

    logger.info("All images merged.")

    # Save the merged image if debug mode is on
    if log_level == "TRACE":
        output_path = os.path.join(output_dir, "debug")
        os.makedirs(output_path, exist_ok=True)
        save_path = os.path.join(output_path, "merged_image.png")
        cv2.imwrite(save_path, final_image)

    return final_image

def slice_image_in_tiles(image_path, tile_height, tile_width, target_max_dim, overlap, number, output_dir, log_level):
    """
    Generates overlapping image tiles (sliding window) using NumPy slicing.
    Returns a list of tile information dictionaries.
    """
    img, width, height = image_path

    if img is None:
        raise FileNotFoundError(f"Image not found at {image_path}")

    tiles = []

    stride_y = tile_height - overlap
    stride_x = tile_width - overlap
    if stride_y <= 0: stride_y = tile_height
    if stride_x <= 0: stride_x = tile_width

    # Iterate through the image using strides
    for top in range(0, height, stride_y):
        for left in range(0, width, stride_x):
            # Ensure tiles stay within image boundaries
            # Adjust top/left if the edge tile goes out of bounds
            effective_top = top
            effective_left = left
            if top + tile_height > height:
                effective_top = height - tile_height
            if left + tile_width > width:
                effective_left = width - tile_width
            
            # Ensure coordinates don't become negative
            effective_top = max(0, effective_top)
            effective_left = max(0, effective_left)

            # Extract the tile using NumPy slicing
            tile_img_np = img[effective_top:effective_top+tile_height, effective_left:effective_left+tile_width]

            # Resize if size is larger than target max dimension
            original_tile_h, original_tile_w, _ = tile_img_np.shape
            scale_x = 1
            scale_y = 1

            if original_tile_h != target_max_dim or original_tile_w != target_max_dim:
                tile_img_np = cv2.resize(tile_img_np, (target_max_dim, target_max_dim), interpolation=(cv2.INTER_AREA if original_tile_w > target_max_dim else cv2.INTER_LANCZOS4))

                # Calculate scaling factors
                resized_tile_h, resized_tile_w, _ = tile_img_np.shape
                scale_x = original_tile_w / resized_tile_w
                scale_y = original_tile_h / resized_tile_h

            tiles.append({
                'image': tile_img_np, 
                'top_offset': effective_top, 
                # 'bottom_offset': effective_top + tile_height, 
                'left_offset': effective_left,
                # 'right_offset': effective_left + tile_width,
                'scale_x': scale_x,
                'scale_y': scale_y
            })
            
            # Break inner loop if we are at the right edge
            if left + tile_width >= width:
                break
        
        # Break outer loop if we are at the bottom edge
        if top + tile_height >= height:
            break

    # Save image tiles if debug mode is on
    if log_level == "TRACE":
        output_path = f"{output_dir}/debug/tile"
        os.makedirs(output_path, exist_ok=True)
        for i, slice in enumerate(tiles):
            image_slice = slice["image"]
            save_path = f"{output_path}/tile{number}_{i:02d}.jpg"
            cv2.imwrite(save_path, image_slice, [cv2.IMWRITE_JPEG_QUALITY, 100])

    return tiles


def crop_out_box(box, image, resize, output_dir, crop_name, log_level):

    [xmin, ymin, xmax, ymax] = box
    use_upscaler, upscale_ratio = resize

    # Ensure coordinates are valid for cropping
    xmin, ymin, xmax, ymax = max(0, xmin), max(0, ymin), min(image.shape[1], xmax), min(image.shape[0], ymax)

    # Crop the detection from the original image
    cropped_img = image[ymin:ymax, xmin:xmax].copy()

    # --- Resizing while maintaining aspect ratio for OCR input ---
    h, w, c = cropped_img.shape

    # Upscale cropped image if enabled
    if use_upscaler:
        new_w = int(w * upscale_ratio)
        new_h = int(h * upscale_ratio)
        cropped_img = cv2.resize(cropped_img, (new_w, new_h), interpolation=(cv2.INTER_AREA if w > new_w else cv2.INTER_LANCZOS4))

    # cropped_img_rgb = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB)

    if log_level == "TRACE":
        save_path = f"{output_dir}/debug/crop"
        os.makedirs(save_path, exist_ok=True)
        cv2.imwrite(f"{save_path}/{crop_name}", cropped_img, [cv2.IMWRITE_JPEG_QUALITY, 100])

    return cropped_img


def split_image_safely(image: tuple, detections: list[dict], max_height: int, output_dir, log_level):
    """
    Split image using cv2 (NumPy slicing) on non-text areas.
    """
    logger.info("\nSplitting image on non-text areas using OpenCV.")

    image_array, width, height = image
    split_points = [0]
    current_pos = 0
    offset = 20

    # Extract boxes; assumes format like detections[i]["box"] = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    forbidden_zones = []
    for d in detections:
        box = d["box"]
        # Use y-coordinates from the detection box
        y_min = max(0, box[0][1] - offset)
        y_max = min(height, box[2][1] + offset)
        forbidden_zones.append((y_min, y_max))

    while current_pos < height:
        target_y = min(current_pos + max_height, height)
        
        if target_y == height:
            split_points.append(height)
            break

        best_split = -1
        # Look backwards for a safe gap
        for y in range(target_y, current_pos, -1):
            if not any(y_min < y < y_max for y_min, y_max in forbidden_zones):
                best_split = y
                break

        # Fallback if no safe gap is found
        if best_split == -1:
            best_split = target_y
            
        split_points.append(best_split)
        current_pos = best_split

    # Perform slicing (cropping)
    chunks = []
    for i in range(len(split_points) - 1):
        y_start, y_end = split_points[i], split_points[i + 1]
        if y_end > y_start:
            # OpenCV slicing: image[y_start:y_end, x_start:x_end]
            # .copy() is recommended if you need independent arrays
            chunk = image_array[y_start:y_end, 0:width].copy() 
            chunk_rgb = cv2.cvtColor(chunk, cv2.COLOR_BGR2RGB)
            chunks.append({
                "image": chunk_rgb,
                "top_offset": y_start,
            })

    logger.info(f"Image split into {len(chunks)} parts.")

    return chunks, range(len(chunks))


def create_inpainting_mask(image: object, box: list[int]):
    """
    Creates a binary mask for inpainting from a bounding box.
    """

    xmin, ymin, xmax, ymax = box

    # Create a black mask image with the same height and width as the original image
    # and a single channel (grayscale)
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    # Fill the specified bounding box region with white pixels (255)
    # With numpy slicing
    mask[ymin:ymax, xmin:xmax] = 255
    # Or with cv2.rectangle
    # cv2.rectangle(mask, (xmin, ymin), (xmax, ymax), 255, -1)

    return mask