import os
import threading
import numpy as np
from PIL import Image
from tqdm import tqdm
import onnxruntime as ort
from loguru import logger
from colorama import init, Fore
from concurrent.futures import ThreadPoolExecutor

from app.core.model import download_repo_snapshot


init(autoreset=True)
lock = threading.Lock()

def get_bbox_coords(points: list[list]):
    """Helper to get min/max coordinates and center from points."""
    points_np = np.array(points)
    min_x, min_y = np.min(points_np, axis=0)
    max_x, max_y = np.max(points_np, axis=0)
    center_y = (min_y + max_y) / 2
    return min_x, min_y, max_x, max_y, center_y

class TextAreaDetection:
    """
    A class to handle text area detection.

    :param model_path: Path to the onnx model file.

    :return: A list of dictionary containing bounding boxes among others.
    """
    def __init__(self, confidence_threshold: float, use_gpu: bool):
        """
        Initializes detection model.
        """
        logger.info(f"Initializing detection model.")

        self.repo_id="ogkalu/comic-text-and-bubble-detector"
        self.file_name="detector.onnx"
        self.snapshot_path=f"models/detection/{self.repo_id}"
        self.model_path=f"{self.snapshot_path}/{self.file_name}"

        # Download detection model if not exist
        if not os.path.exists(self.model_path):
            download_repo_snapshot(repo_id=self.repo_id, local_dir=self.snapshot_path)

        self.confidence_threshold = confidence_threshold

        self.classes = {
            0: 'bubble',
            1: 'text_bubble',
            2: 'text_free'
        }

        if use_gpu:
            self.providers = [
                "CUDAExecutionProvider",
                "TensorrtExecutionProvider",
                "MIGraphXExecutionProvider",
                "OpenVINOExecutionProvider",
                "QNNExecutionProvider",
                "CPUExecutionProvider"
            ]
        else:
            self.providers = ["CPUExecutionProvider"]

        # Define the number of threads
        self.num_threads = int(os.cpu_count()/2) or 1

        session_options = ort.SessionOptions()
        session_options.inter_op_num_threads = self.num_threads # For parallel model execution
        session_options.intra_op_num_threads = self.num_threads # For parallel computation inside each operator

        self.session = ort.InferenceSession(self.model_path, sess_options=session_options, providers=self.providers)

        if not self.session:
            raise Exception(Fore.RED + "Failed to initialize detection model!")

        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]

        logger.info("Detection model initialized.\n")

    def detect_text_areas(self, image_name: str, number: int, slice: dict | object, target_sizes: list[int], log_level: str, image_tiled: bool) -> list[dict]:
        """Runs detection on each tile and adjusts coordinates to original image space."""

        result_list = []

        # with lock:
        if image_tiled:
            slice_img_np = np.array(slice["image"])
            top_offset = slice["top_offset"]
            left_offset = slice["left_offset"]
            scale_x = slice['scale_x']
            scale_y = slice['scale_y']
        else:
            logger.info(f"Detecting text areas with ogkalu/comic-text-and-bubble-detector.onnx")

            slice_img_np = np.array(slice)
            top_offset = 0
            left_offset = 0
            scale_x = 1
            scale_y = 1

        slice_float32 = slice_img_np.astype(np.float32) / 255.0
        slice_transposed = slice_float32.transpose(2, 0, 1)
        slice_batchd = np.expand_dims(slice_transposed, axis=0)
        # Run inference
        results = self.session.run(
            self.output_names, {"images": slice_batchd, "orig_target_sizes": np.array([target_sizes], dtype=np.int64)}
        )

        labels, boxes, scores = results[:3]

        if isinstance(labels, np.ndarray) and labels.ndim == 2 and labels.shape[0] == 1:
            labels = labels[0]
        if isinstance(scores, np.ndarray) and scores.ndim == 2 and scores.shape[0] == 1:
            scores = scores[0]
        if isinstance(boxes, np.ndarray) and boxes.ndim == 3 and boxes.shape[0] == 1:
            boxes = boxes[0]

        if results:
            n = 0
            for lab, box, scr in zip(labels, boxes, scores):
                # Filter out lower confidence
                if float(scr) < float(self.confidence_threshold):
                    continue
                # Skip bubble only detections
                if lab == 0:
                    continue
                label_name = self.classes[lab]
                # Convert bbox to four-corner coordinates
                xmin, ymin, xmax, ymax = box

                top_left = [xmin, ymin]
                top_right = [xmax, ymin]
                bottom_right = [xmax, ymax]
                bottom_left = [xmin, ymax]

                corners = [top_left, top_right, bottom_right, bottom_left]

                # Adjust coordinates back to the original slice size (inverse scaling) and then to the original full image coordinate system (offsets)
                adjusted_points = [[(int(p[0]) * scale_x) + left_offset, (int(p[1]) * scale_y) + top_offset] for p in corners]

                _, _, _, _, center_y = get_bbox_coords(adjusted_points)

                result = {
                    "box": np.array(adjusted_points, dtype=np.int32),
                    "confidence": float(scr),
                    "original_text": "",
                    "text_confidence": 0,
                    "translated_text": "",
                    "center_y": center_y,
                    "image_name": image_name,
                    "number": number
                }

                if log_level == "TRACE":
                    logger.info(f"({scr:.2f}) {label_name} {adjusted_points}")
                n+=1

                result_list.append(result)

        return result_list

    def batch_threaded(self, image_name: str, images: dict | object, target_sizes: list[int], log_level: str, image_tiled: bool):
        """Manages thread pool for batch detection"""

        all_results = []

        logger.info(f"\nDetecting text areas with ogkalu/comic-text-and-bubble-detector.onnx in {self.num_threads} threads.")

        # Use ThreadPoolExecutor for concurrent execution
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            number = len(images)
            # Use executor.map() to get results in correct order. It's slower than as_completed() tho.
            futures = executor.map(self.detect_text_areas, [image_name]*number, range(number), images, [target_sizes]*number, [log_level]*number, [image_tiled]*number)

            for future in tqdm(futures, total=len(images), desc="Detection"):
                if future:
                    all_results.extend(future)

        # Return the populated, thread-safe results dictionary
        return all_results


def calculate_iou_2d(box1: tuple[int], box2: tuple[int]):
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


def merge_overlapping_boxes(results: list[dict], det_merge_threshold: float) -> list[dict]:
    if not results: return []

    merged_blocks = []
    for current in results:
        merged = False
        current_bbox_coords = get_bbox_coords(current['box'])
        c_min_x, c_min_y, c_max_x, c_max_y, _ = current_bbox_coords
        for existing_block in merged_blocks:
            existing_bbox_coords = get_bbox_coords(existing_block['box'])
            e_min_x, e_min_y, e_max_x, e_max_y, _ = existing_bbox_coords

            IoU = calculate_iou_2d(current_bbox_coords, existing_bbox_coords)

            if IoU > det_merge_threshold:
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