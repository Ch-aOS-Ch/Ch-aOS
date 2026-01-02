import os
import subprocess
from omegaconf import OmegaConf

"""
This is quite literally a tiny script to open the Ch-obolo file in the user's preferred text editor.
"""
def runChoboloEdit(chobolo_path):
    editor = os.getenv('EDITOR', 'nano')
    if not chobolo_path:
        CONFIG_DIR = os.path.expanduser("~/.config/chaos")
        CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
        if not os.path.exists(CONFIG_FILE_PATH):
            raise FileNotFoundError("No chaos config file found, and no chobolo path provided.")
        cfg = OmegaConf.load(CONFIG_FILE_PATH)
        chobolo_path = cfg.get('chobolo_file', None)

    if chobolo_path:
        try:
            subprocess.run(
                [editor, chobolo_path],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Ch-obolo editing failed. Editor exited with error code {e.returncode}.") from e
        except FileNotFoundError:
            raise FileNotFoundError(f"Editor '{editor}' not found. Please ensure it is installed and in your PATH.")
    else:
        raise ValueError("No Ch-obolo file configured to edit.")
