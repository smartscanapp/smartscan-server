from server.config import SmartScanConfig, save_config
from server.constants import SMARTSCAN_CONFIG_PATH

config  = SmartScanConfig()

print(config.similarity_threshold)

config.similarity_threshold = 0.1 

print (config.similarity_threshold)

save_config(SMARTSCAN_CONFIG_PATH, config)