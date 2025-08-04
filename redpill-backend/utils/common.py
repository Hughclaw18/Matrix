import os
from dotenv import load_dotenv

def load_environment_variables():
    load_dotenv()

def get_nvidia_api_key():
    return os.getenv("NVIDIA_API_KEY")

def get_qdrant_config():
    return {
        "host": os.getenv("QDRANT_HOST"),
        "port": os.getenv("QDRANT_PORT"),
        "api_key": os.getenv("QDRANT_API_KEY")
    }