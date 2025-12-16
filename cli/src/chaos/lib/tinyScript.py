import os
import subprocess
from omegaconf import OmegaConf
import sys

def runChoboloEdit(chobolo_path):
    editor = os.getenv('EDITOR', 'nano')
    if not chobolo_path:
        CONFIG_DIR = os.path.expanduser("~/.config/chaos")
        CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
        cfg = OmegaConf.load(CONFIG_FILE_PATH)
        chobolo_path = cfg.get('chobolo_file', None)
    if chobolo_path:
        try:
            subprocess.run(
                [editor, chobolo_path],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print("ERROR: Ch-obolo editing failed.")
            print("Details: Editor exited with error code", e.returncode)
            sys.exit(1)
        except FileNotFoundError:
            print(f"ERROR: Editor '{editor}' not found. Please ensure it is installed and in your PATH.", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: No Ch-obolo file configured to edit.", file=sys.stderr)
        sys.exit(1)
