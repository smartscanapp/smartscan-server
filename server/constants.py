import os 
from smartscan.constants import MODEL_REGISTRY

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Models
CLIP_TEXT_MODEL_PATH = os.path.join(BASE_DIR, 'models/clip_text_encoder_quant.onnx')
CLIP_IMAGE_MODEL_PATH = os.path.join(BASE_DIR, 'models/clip_image_encoder_quant.onnx')
MINILM_MODEL_PATH = os.path.join(BASE_DIR, 'models/minilm_sentence_transformer_quant.onnx')
DINO_V2_SMALL_MODEL_PATH = os.path.join(BASE_DIR, 'models/dinov2_small_quant.onnx')
ULTRA_LIGHT_FACE_DETECTOR_MODEL_PATH = os.path.join(BASE_DIR, 'models/face_detect.onnx')
INCEPTION_RESNET_MODEL_PATH = os.path.join(BASE_DIR, 'models/inception_resnet_v1_quant.onnx')

MODEL_PATHS = {
    MODEL_REGISTRY["clip-vit-b-32-image"]:CLIP_IMAGE_MODEL_PATH,
    MODEL_REGISTRY['dinov2-small']: DINO_V2_SMALL_MODEL_PATH,
    MODEL_REGISTRY['clip-vit-b-32-text']: CLIP_TEXT_MODEL_PATH,
    MODEL_REGISTRY['all-minilm-l6-v2']: MINILM_MODEL_PATH,
}

# DB
DB_DIR = os.path.join(BASE_DIR, "db")

# Config
SMARTSCAN_CONFIG_PATH = os.path.join(BASE_DIR, "smartscan.json")


