import os
from tqdm import tqdm
from loguru import logger
from huggingface_hub import hf_hub_download, snapshot_download

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"

def download_model(repo_id, file_name, local_dir):
    logger.info("\nModel does not exist. Initiating download.")

    local_path = hf_hub_download(
        repo_id=repo_id,
        filename=file_name,
        local_dir=local_dir
    )

    logger.info(f"Model downloaded to: {local_path}")

def download_repo_snapshot(repo_id, local_dir):
    logger.info("\nRepo snapshot does not exist. Initiating download.")

    local_path = snapshot_download(
        repo_id=repo_id,
        local_dir=local_dir
    )

    logger.info(f"Repo snapshot downloaded to: {local_path}")