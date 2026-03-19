import os
from pathlib import Path

from omegaconf import OmegaConf

from .args.dataclasses import SetPayload

"""
Orchestration/Explanation Handlers for Chaos CLI
"""


def setMode(payload: SetPayload):
    """
    Just handles configuring the tool.
    """
    CONFIG_DIR = os.getenv("CHAOS_CONFIG_DIR", Path.home() / ".config" / "chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    print(f"Saving configuration to {CONFIG_FILE_PATH}...")

    os.makedirs(CONFIG_DIR, exist_ok=True)

    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH)
    else:
        global_config = OmegaConf.create()

    if hasattr(payload, "chobolo_file") and payload.chobolo_file:
        inputPath = Path(payload.chobolo_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.chobolo_file = str(absolutePath)
            print(f"- Default Ch-obolo set to: {payload.chobolo_file}")
        except FileNotFoundError:
            raise FileNotFoundError(f"ERROR: File not found in: {inputPath}")

    if hasattr(payload, "secrets_file") and payload.secrets_file:
        inputPath = Path(payload.secrets_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.secrets_file = str(absolutePath)
            print(f"- Default secrets file set to: {payload.secrets_file}")
        except FileNotFoundError:
            raise FileNotFoundError(f"ERROR: File not found in: {inputPath}")

    if hasattr(payload, "sops_file") and payload.sops_file:
        inputPath = Path(payload.sops_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.sops_file = str(absolutePath)
            print(f"- Default sops file set to: {payload.sops_file}")
        except FileNotFoundError:
            raise FileNotFoundError(f"ERROR: File not found in: {inputPath}")

    OmegaConf.save(global_config, CONFIG_FILE_PATH)
    print("Configuration saved.")
