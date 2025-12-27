import os
from tqdm import tqdm
from loguru import logger
from colorama import Fore, Style, init
from huggingface_hub import hf_hub_download, snapshot_download

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"
init(autoreset=True)

def download_model(repo_id: str, file_name: str, local_dir: str):
    logger.info(Style.BRIGHT + Fore.YELLOW + "Model does not exist. Initiating download...")

    local_path = hf_hub_download(
        repo_id=repo_id,
        filename=file_name,
        local_dir=local_dir
    )

    logger.info(Style.BRIGHT + Fore.GREEN + f"Model downloaded to: {local_path}\n")

def download_repo_snapshot(repo_id: str, local_dir: str):
    logger.info(Style.BRIGHT + Fore.YELLOW + "Repo snapshot does not exist. Initiating download...")

    local_path = snapshot_download(
        repo_id=repo_id,
        local_dir=local_dir
    )

    logger.info(Style.BRIGHT + Fore.GREEN + f"Repo snapshot downloaded to: {local_path}\n")