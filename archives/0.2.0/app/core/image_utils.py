import os
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from collections import Counter

def merge_images_vertically(images):
    """
    Merges all images in each subfolder into a single image and saves it 
    in the corresponding output subfolder.
    """

    image_count = len(images)
    print(f"Merging {image_count} images into one.")

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

    print("All images merged.\n")
    return final_image
    # Define the output path
    # output_dir = "result"
    # output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the combined image with a relevant name
    # save_path = output_dir / "combined_image.png"
    # final_image.save(save_path, quality=100)
    # print(f"Merged {len(images)} images in {dirpath} and saved to {save_path}")


def split_image_safely(image, image_width, image_height, detection, max_height=30000):
    """
    Split image on non-text areas.
    """
    img = image
    width = image_width
    height = image_height
    boxes = detection
    split_points = [0]
    current_pos = 0

    print("\nSplitting image on non-text areas.")
    while current_pos < height:
        # Determine the maximum possible safe height for the current chunk
        max_safe_y = min(current_pos + max_height, height)
        
        # Look for a safe split point within the allowed range (e.g., in a margin)
        # For simplicity here, we look for a y-coordinate that doesn't intersect any bubble
        
        best_split = max_safe_y
        
        # Iterate backwards from max_safe_y to find a safe boundary
        for y in range(max_safe_y, current_pos, -1):
            is_safe = True
            for box in boxes:
                # box is [x_min, y_min, x_max, y_max]
                y_min, y_max = box[1], box[3]
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
        y_end = split_points[i+1]
        if y_end > y_start:
            chunk = img.crop((0, y_start, width, y_end))
            chunks.append(chunk)
            # chunk.save(f"output_chunk_{i+1}.png")

    chunks_total = len(chunks)
    chunks_number = range(chunks_total)
    print(f"Image splitted into {chunks_total} parts.\n")

    return chunks, chunks_number