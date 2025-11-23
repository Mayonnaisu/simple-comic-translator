import numpy as np
from paddleocr import PaddleOCR

def process_region_with_ocr(chunks, ocr_lang, slice, gpu_mode):
    """
    Checks region size, tiles if necessary, and runs PaddleOCR.
    Offsets are used to remap coordinates back to the original image.
    Returns a list of [remapped_points_list, (text, confidence)].
    """
    results_list = []
    chunks_np = [np.asarray(chunk) for chunk in chunks]

    print("Extracting texts with PaddleOCR.")

    ocr_instance  = PaddleOCR(
        use_angle_cls=True,
        lang=ocr_lang,
        use_gpu=gpu_mode,
        show_log=False,
        det_db_thresh=0.3,
        det_db_box_thresh=0.6
    )

    kwargs = {
        "cls": False,
        "det": True,
        "rec": True,
    }

    if slice:
        kwargs["slice"] = {
            "horizontal_stride": 1200,
            "vertical_stride": 400,
            "merge_x_thres": 30,
            "merge_y_thres": 30,
        }

    for i, chunk in enumerate(chunks_np):
        chunk_name = f"image_{str(i).zfill(2)}"
        ocr_result = ocr_instance.ocr(
            chunk,
            **kwargs
        )
        for line in ocr_result:
            if line:
                for detection in line:
                    box_coords = detection[0]
                    text_info = detection[1]
                    text = text_info[0] 
                    score = text_info[1]
                    results_list.append(
                        {
                            "box": np.array(box_coords),
                            "original_text": text,
                            "confidence": score,
                            "translated_text": "",
                            "image_name": chunk_name
                        }
                    )
                    print(f"({score:.2f}) {text} {box_coords}")

    return results_list

def merge_boxes_and_text(box1, text1, box2, text2):
    """Merges two boxes and concatenates text."""
    # box format: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]] -> needs conversion to [x_min, y_min, x_max, y_max]
    b1_flat = [
        np.min(box1[:, 0]),
        np.min(box1[:, 1]),
        np.max(box1[:, 0]),
        np.max(box1[:, 1]),
    ]
    b2_flat = [
        np.min(box2[:, 0]),
        np.min(box2[:, 1]),
        np.max(box2[:, 0]),
        np.max(box2[:, 1]),
    ]

    new_box_flat = [
        min(b1_flat[0], b2_flat[0]),
        min(b1_flat[1], b2_flat[1]),
        max(b1_flat[2], b2_flat[2]),
        max(b1_flat[3], b2_flat[3]),
    ]
    # Return as numpy array in the original 4-point format (for consistency, although we use flat format later)
    # The new box is treated as a simple upright rectangle
    new_box = np.array(
        [
            [new_box_flat[0], new_box_flat[1]],
            [new_box_flat[2], new_box_flat[1]],
            [new_box_flat[2], new_box_flat[3]],
            [new_box_flat[0], new_box_flat[3]],
        ]
    )

    # Sort text logically (top-to-bottom, left-to-right is hard with angle, generally a space works)
    new_text = f"{text1} {text2}"
    return new_box, new_text


def merge_nearby_boxes(ocr_results, y_threshold, chunks_number):
    """Groups text lines that are close vertically into single items."""
    if not ocr_results:
        return []

    merged_list = []

    # Sort items primarily by Y coordinate (top to bottom)
    for i in chunks_number:
        detected_items = []
        name = f"image_{str(i).zfill(2)}"
        for ocr in ocr_results:
            if ocr["image_name"] == name:
                detected_items.append(ocr)

        detected_items.sort(key=lambda x: np.min(x["box"][:, 1]))

        if detected_items:
            current_group = detected_items[0]

            for next_item in detected_items[1:]:
                # Get Y coordinates of current and next item
                current_y_max = np.max(current_group["box"][:, 1])
                next_y_min = np.min(next_item["box"][:, 1])

                # Check if the vertical gap is less than the threshold
                if (next_y_min - current_y_max) < y_threshold:
                    # Merge the boxes and text
                    new_box, new_text = merge_boxes_and_text(
                        current_group["box"],
                        current_group["original_text"],
                        next_item["box"],
                        next_item["original_text"],
                    )
                    current_group["box"] = new_box
                    current_group["original_text"] = new_text
                else:
                    # The gap is too large, finalize the current group and start a new one
                    merged_list.append(current_group)
                    current_group = next_item

            # Append the last group after the loop finishes
            merged_list.append(current_group)

    return merged_list