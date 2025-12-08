import numpy as np
from tqdm import tqdm
from loguru import logger
from typing import List, Dict
from natsort import natsorted
from paddleocr import PaddleOCR
# from paddleocr.tools.infer.predict_system import sorted_boxes


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

    for i, slice_info in enumerate(slices):
        slice_name = f"image_{i:02d}"
        try:
            slice_img_np = slice_info["image"]
            top_offset = slice_info["top_offset"]
            left_offset = slice_info["left_offset"]
        except Exception:
            slice_img_np = slice_info
            top_offset = 0
            left_offset = 0

        result = ocr_instance.ocr(
            np.array(slice_img_np),
            **kwargs
        )

        if result and result[0]:
            for n, line in enumerate(result[0]):
                # PaddleOCR result format: [[point1, point2, ...], (text, confidence)]
                confidence = line[1][1]

                # Filter out lower confidence
                if confidence < 0.9:
                    continue

                points = line[0]
                text = line[1][0]

                # Adjust coordinates to the original image's coordinate system
                adjusted_points = [[p[0] + left_offset, p[1] + top_offset] for p in points]
                _, _, _, _, center_y = get_bbox_coords(adjusted_points)

                all_results.append(
                    {
                        "box": np.array(adjusted_points),
                        "original_text": text,
                        "confidence": confidence,
                        "center_y": center_y,
                        "translated_text": "",
                        "image_name": slice_name,
                        "number": n,
                        "duplicate": {}
                    }
                )

                if log_level == "INFO":
                    logger.info(f"({n}) {text} {adjusted_points}")

    return all_results

def calculate_iou_2d(box1, box2):
    """
    Calculates 2D Intersection over Union (IoU) for two upright bounding boxes.
    Box format is (xmin, ymin, xmax, ymax).
    """
    xmin1, ymin1, xmax1, ymax1, _ = box1
    xmin2, ymin2, xmax2, ymax2, _ = box2

    # Calculate intersection coordinates
    inter_xmin = max(xmin1, xmin2)
    inter_ymin = max(ymin1, ymin2)
    inter_xmax = min(xmax1, xmax2)
    inter_ymax = min(ymax1, ymax2)

    # Calculate intersection area
    inter_width = max(0, inter_xmax - inter_xmin)
    inter_height = max(0, inter_ymax - inter_ymin)
    inter_area = inter_width * inter_height

    # Calculate the area of both individual boxes
    area1 = (xmax1 - xmin1) * (ymax1 - ymin1)
    area2 = (xmax2 - xmin2) * (ymax2 - ymin2)

    # Calculate the union area
    union_area = area1 + area2 - inter_area
    
    if union_area == 0:
        return 0.0

    return inter_area / union_area


def deduplicate_results_2d(results: List[Dict], iou_threshold, stage) -> List[Dict]:
    """
    Removes duplicate detections from overlapping tiles using 2D IoU check.
    Processes high-confidence boxes first.
    """
    if not results:
        return []

    # Sort results by confidence score descending, then by Y position
    # results.sort (key=lambda r: (r['image_name'], min(p[1] for p in r['box']), r['confidence']))

    unique_results = []
    for i, current_res in enumerate(results):
        is_duplicate = False
        current_bbox_coords = get_bbox_coords(current_res['box'])

        for unique_res in unique_results:
            unique_bbox_coords = get_bbox_coords(unique_res['box'])
            
            # Use 2D IOU to check overlap in both X and Y dimensions
            if calculate_iou_2d(current_bbox_coords, unique_bbox_coords) > iou_threshold:
                # If they overlap significantly, assume they are the same detection.
                if current_res['confidence'] > unique_res['confidence']:
                    results[i] = current_res
                else:
                    results[i] = unique_res

                is_duplicate = True
                break

        if not is_duplicate:
            # Keep only unique, high-confidence results
            unique_results.append(current_res)

    # Re-sort unique results top-to-bottom, left-to-right for subsequent merging
    # unique_results.sort(key=lambda r: (r['image_name'], min(p[0] for p in r['box']), min(p[1] for p in r['box'])))
    # sorted_unique_results = sorted_boxes(unique_results)
    # sorted_unique_results = natsorted(unique_results, key=lambda r: (r['image_name'], r['number']))
    # for group in duplicate_groups:
    #     print(group)
    #     if group["duplicate"]:
    #         if group["confidence"] > group["duplicate"]["confidence"]:
    #             del group["duplicate"]
    #             unique_results.append(group)
    #         else:
    #             unique_results.append(group["duplicate"])
    #     else:
    #         unique_results.append(group)
    if stage == 1:
        return results
    elif stage == 2:
        return unique_results


def merge_nearby_boxes(results, y_threshold_pixels, x_threshold_pixels):
    if not results: return []
    # results.sort(key=lambda r: (min(p[0] for p in r['box']), min(p[1] for p in r['box'])))
    merged_blocks = []
    for current in results:
        merged = False
        for existing_block in merged_blocks:
            e_min_x, e_min_y, e_max_x, e_max_y, _ = get_bbox_coords(existing_block['box'])
            c_min_x, c_min_y, c_max_x, c_max_y, _ = get_bbox_coords(current['box'])
            vertical_gap = c_min_y - e_max_y
            horizontal_overlap_or_gap = max(e_min_x, c_min_x) < min(e_max_x, c_max_x) + x_threshold_pixels
            if vertical_gap < y_threshold_pixels and horizontal_overlap_or_gap: 
                existing_block['original_text'] += " " + current['original_text']
                new_min_x, new_min_y = min(e_min_x, c_min_x), min(e_min_y, c_min_y)
                new_max_x, new_max_y = max(e_max_x, c_max_x), max(e_max_y, c_max_y)
                existing_block['box'] = [[new_min_x, new_min_y], [new_max_x, new_min_y], [new_max_x, new_max_y], [new_min_x, new_max_y]]
                existing_block['center_y'] = (new_min_y + new_max_y) / 2
                merged = True
                break
        if not merged:
            merged_blocks.append(current)
    return merged_blocks