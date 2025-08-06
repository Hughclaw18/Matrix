import os
from dotenv import load_dotenv

def load_environment_variables():
    load_dotenv()

def get_nvidia_api_key():
    return os.getenv("NVIDIA_API_KEY")