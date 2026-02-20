import json
import numpy as np
from loguru import logger


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        # Convert NumPy arrays to lists
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        # Convert NumPy integers (int32, int64) to Python int
        if isinstance(obj, np.integer):
            return int(obj)
        # Convert NumPy floats (float32, float64) to Python float
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)


def save_result_json(result_json_path: str, translated_text_data: list[dict]):
    with open(result_json_path, 'w', encoding='utf-8') as f:
        json.dump(translated_text_data, f, cls=NumpyEncoder, ensure_ascii=False, indent=4)


def load_result_json(result_json_path: str, memory: list[object|str|bool]):
    logger.info(f"\nLoading existing result.json...")

    tm, overwrite_memory, source_language, target_language = memory

    with open(result_json_path, "r", encoding="utf-8") as f:
        loaded_result_json = json.load(f)

    for item in loaded_result_json:
        # Convert bounding boxes back to NumPy arrays
        item["box"] = np.array(item["box"], dtype=np.int32)
        # Overwrite or keep translation memory
        if overwrite_memory:
            tm.add_translation(item["original_text"], source_language, item["translated_text"], target_language, overwrite_memory)

    logger.success(f"Existing result.json loaded.")

    return loaded_result_json