import os
import json
from dotenv import load_dotenv

load_dotenv()
env = os.getenv

# Model mapping
MODEL_OPTIONS = {
    'Claude 3 Haiku': 'us.anthropic.claude-3-haiku-20240307-v1:0',
    'Claude 3 Sonnet': 'us.anthropic.claude-3-sonnet-20240229-v1:0',
    'Claude 3 Opus': 'us.anthropic.claude-3-opus-20240229-v1:0',
    }

# Streamlit defaults
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 1.0

# Load server configuration
config_path = os.path.join('.', 'servers_config.json')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        SERVER_CONFIG = json.load(f)