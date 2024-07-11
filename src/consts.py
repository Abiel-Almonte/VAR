from pathlib import Path
from prompt import IMG_PROMPT

MODEL= str(Path.home()) + "/workspace/quantized_models/Mistral-7B-Instruct-v0.3-awq-IMG"
IMAGE_FOLDER= str(Path.home())+ "/workspace/Flickr30k/flickr30k_images/flickr30k_images"
CSV_FOLDER= str(Path.home()) + "/workspace/Flickr30k/flickr30k_images/results.csv"
CLIP_MODEL= "openai/clip-vit-large-patch14"
CLIP_COMP_DIM= 1536 #768*2
DTYPE= 'float16'
GPU_UTIL= 0.8
MAX_LEN= 8192
MAX_TOKENS=2048
IMG_TOKEN= 32768
TEMP= 0.0

