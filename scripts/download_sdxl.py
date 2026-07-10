import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from download_models import download_file

url = "https://huggingface.co/RunDiffusion/Juggernaut-XL-v8/resolve/main/juggernautXL_v8Rundiffusion.safetensors"
dest = Path("/app/models/checkpoints/juggernautXL_v8Rundiffusion.safetensors")
download_file(url, dest, description="sdxl")
