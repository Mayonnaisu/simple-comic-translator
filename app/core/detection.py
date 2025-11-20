import os
import torch
from sahi.auto_model import AutoDetectionModel
from sahi.predict import get_sliced_prediction

def detect_text_areas(image_path, image_width, slice_height, export_visuals, output_dir, gpu_mode):
    """
    Detects text areas.
    """
    boxes = []

    if gpu_mode:
        if torch.cuda.is_available():
            device = "cuda:0"
        elif torch.xpu.is_available():
            device = "xpu:0"
    else:
        device = "cpu"

    detection_model = AutoDetectionModel.from_pretrained(
        model_type='yolov8',
        model_path='models/detection/ogkalu/comic-speech-bubble-detector-yolov8m/comic-speech-bubble-detector.pt',
        confidence_threshold=0.5,
        device=device
    )

    results = get_sliced_prediction(
        image_path,
        detection_model,
        slice_height=slice_height,
        slice_width=image_width,
        overlap_height_ratio=0.2,
        overlap_width_ratio=0.2,
        verbose=1,
    )
    object_prediction_list = results.object_prediction_list

    # Extract bounding boxes
    for result in object_prediction_list:
        # Get coordinates in the format [x_min, y_min, x_max, y_max]
        coords = result.bbox.to_xyxy()
        boxes.append(coords)
        print(result)

    print(f"Found {len(object_prediction_list)} text areas.")

    if export_visuals:
        output_dir = f"{output_dir}/output_visuals"
        os.makedirs(output_dir, exist_ok=True)

        results.export_visuals(rect_th=2, text_size=10, hide_labels=True, hide_conf=True, export_dir=output_dir)

        print(f"Visualizations saved to {output_dir}")

    return boxes