from pathlib import Path
from .prompt import IMG_PROMPT


workspace_path = Path.home() / "workspace"
flickr_path = workspace_path / "Flickr30k/flickr30k_images"

MODEL= workspace_path / "quantized_models/Mistral-7B-Instruct-v0.3-awq-IMG"
IMAGE_FOLDER= flickr_path / "flickr30k_images"
CSV_FOLDER= flickr_path / "results.csv"

MODEL = str(MODEL)
IMAGE_FOLDER = str(IMAGE_FOLDER)
CSV_FOLDER = str(CSV_FOLDER)

CLIP_MODEL= "openai/clip-vit-large-patch14"
CLIP_COMP_DIM= 1536 #768*2
DTYPE= 'float16'
GPU_UTIL= 0.8
MAX_LEN= 8192
MAX_TOKENS=2048
IMG_TOKEN= 32768
TEMP= 0.0

