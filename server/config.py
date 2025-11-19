import json
from dataclasses import dataclass, field, asdict
from smartscan.types import ModelName

@dataclass
class SmartScanConfig:
    similarity_threshold: float = 0.7
    target_dirs: list[str] = field(default_factory=list)
    image_encoder_model: ModelName = 'dinov2-small'
    text_encoder_model: ModelName = 'all-minilm-l6-v2'

def load_config(path: str) -> SmartScanConfig:
    try:
        with open(path, "r") as f:
            config = json.load(f)
        
        default = SmartScanConfig()
        for (key, value) in asdict(default).items():
            config.setdefault(key, value)
        return SmartScanConfig(**config)
    except:
        return SmartScanConfig()
    
    
def save_config(path: str, config: SmartScanConfig):
    try:
        with open(path, "w") as f:
            json.dump(asdict(config), f)
    except:
        pass
