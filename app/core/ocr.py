import numpy as np
from loguru import logger
from paddleocr import PaddleOCR
from tqdm import tqdm


def get_bbox_coords(points):
    """Helper to get min/max coordinates and center from points."""
    points_np = np.array(points)
    min_x, min_y = np.min(points_np, axis=0)
    max_x, max_y = np.max(points_np, axis=0)
    center_y = (min_y + max_y) / 2
    return min_x, min_y, max_x, max_y, center_y


def run_ocr_on_slices(slices, language, use_gpu, use_slicer, process, log_level):
    """Runs PaddleOCR on slices and adjusts coordinates to original image space."""

    logger.info("Extracting texts with PaddleOCR.") if process == "ocr" else logger.info("Detecting text areas with PaddleOCR.")

    all_results = []

    enable_slicer, h_stride, v_stride = use_slicer

    # Initialize the OCR engine
    ocr_instance = PaddleOCR(
        ocr_version='PP-OCRv4',
        lang=language, 
        use_angle_cls=True,
        use_gpu=use_gpu,
        show_log=False)
    
    # Define additional arguments for accomodating slicer
    kwargs = {
        "cls": False,
        "det": True,
        "rec": True,
    }

    if enable_slicer:
        kwargs["slice"] = {
            "horizontal_stride": h_stride,
            "vertical_stride": v_stride,
            "merge_x_thres": 30,
            "merge_y_thres": 30,
        }

    for i, slice_info in enumerate(tqdm(slices)):
        slice_name = f"image_{i:02d}"
        try:
            slice_img_np = slice_info["image"]
            top_offset = slice_info["top_offset"]
        except Exception:
            slice_img_np = slice_info
            top_offset = 0

        result = ocr_instance.ocr(
            np.array(slice_img_np),
            **kwargs
        )

        if result and result[0]:
            for line in result[0]:
                # PaddleOCR result format: [[point1, point2, ...], (text, confidence)]
                confidence = line[1][1]

                # Filter out lower confidence
                if confidence < 0.6:
                    continue

                points = line[0]
                text = line[1][0]

                # Adjust coordinates to the original image's coordinate system
                adjusted_points = [[p[0], p[1] + top_offset] for p in points]
                _, _, _, _, center_y = get_bbox_coords(adjusted_points)

                all_results.append(
                    {
                        "box": np.array(adjusted_points),
                        "original_text": text,
                        "confidence": confidence,
                        "center_y": center_y,
                        "translated_text": "",
                        "image_name": slice_name,
                    }
                )

                if log_level == "TRACE":
                    logger.debug(f"({confidence:.2f}) {text} {adjusted_points}")

    return all_results


def calculate_iou_vertical(box1, box2):
    """Calculate Intersection over Union (IoU) for vertical overlap."""
    _, y1_min, _, y1_max, _ = box1
    _, y2_min, _, y2_max, _ = box2

    intersection_min = max(y1_min, y2_min)
    intersection_max = min(y1_max, y2_max)

    if intersection_max <= intersection_min:
        return 0

    intersection_area = intersection_max - intersection_min
    area1 = y1_max - y1_min
    area2 = y2_max - y2_min

    # Use the smaller area for denominator to ensure high IOU for near matches
    union_area = max(area1, area2)
    if union_area == 0:
        return 0

    return intersection_area / union_area


def deduplicate_results(results, iou_threshold=0.5):
    """
    Removes exact or near-duplicate detections from overlapping slices.

    Uses vertical IOU to identify potential overlaps and then compares text content to avoid duplication.
    """
    if not results:
        return []

    unique_results = []

    for current_res in results:
        is_duplicate = False
        current_bbox = get_bbox_coords(current_res["box"])

        for unique_res in unique_results:
            unique_bbox = get_bbox_coords(unique_res["box"])

            # Check for significant vertical overlap
            if calculate_iou_vertical(current_bbox, unique_bbox) > iou_threshold:
                # Check if the text is essentially the same (simple substring check for fragments)
                if (
                    current_res["original_text"] in unique_res["original_text"]
                    or unique_res["original_text"] in current_res["original_text"]
                ):
                    is_duplicate = True
                    break
                # If they overlap spatially but have different text, they might be adjacent lines.
                # The current logic will treat them as separate lines.

        if not is_duplicate:
            unique_results.append(current_res)

    # Note: This strategy handles *complete* text repetitions well.
    # Merging *fragments* of a single line of text across slices (e.g., "Hello wor" and "rld")
    # is much more complex and usually requires the automated slice operator.

    return unique_results


def merge_boxes_and_text(box1, text1, box2, text2):
    """
    Merges two boxes and concatenates text.
    """
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


def merge_nearby_boxes(ocr_results, y_threshold, x_threshold, process):
    """
    Groups text lines that are close vertically into single items
    """
    if not ocr_results:
        return []

    merged_list = []

    current_group = ocr_results[0]

    for next_item in ocr_results[1:]:
        # Get Y coordinates of current and next item
        current_y_max = np.max(current_group["box"][:, 1])
        next_y_min = np.min(next_item["box"][:, 1])

        e_min_x, _, e_max_x, _, _ = get_bbox_coords(current_group["box"])
        c_min_x, _, c_max_x, _, _ = get_bbox_coords(next_item["box"])

        # Check if the vertical and horizontal gaps are less than the threshold
        vertical_gap = next_y_min - current_y_max
        horizontal_overlap_or_gap = (
            max(e_min_x, c_min_x) < min(e_max_x, c_max_x) + x_threshold
        )

        if vertical_gap < y_threshold and horizontal_overlap_or_gap:
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

    if process == "detection":
        logger.success(f"Found {len(merged_list)} detections.")
    else:
        logger.success(f"Extracted {len(merged_list)} texts.")

    return merged_list