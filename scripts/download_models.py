import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
CHECKPOINTS_DIR = MODELS_DIR / "checkpoints"
CUSTOM_NODES_DIR = BASE_DIR / "custom_nodes"

MODELS = {
    "sdxl": {
        "url": "https://huggingface.co/RunDiffusion/Juggernaut-XL-v8/resolve/main/juggernautXL_v8Rundiffusion.safetensors",
        "path": CHECKPOINTS_DIR / "juggernautXL_v8Rundiffusion.safetensors",
        "size_gb": 6.9,
    },
    "flux_nf4": {
        "url": "https://huggingface.co/lllyasviel/flux1-dev-bnb-nf4/resolve/main/flux1-dev-bnb-nf4-v2.safetensors",
        "path": CHECKPOINTS_DIR / "flux1-dev-bnb-nf4-v2.safetensors",
        "size_gb": 11.9,
    },
}

PLUGINS = {
    "bitsandbytes_nf4": {
        "repo": "https://github.com/comfyanonymous/ComfyUI_bitsandbytes_NF4.git",
        "path": CUSTOM_NODES_DIR / "ComfyUI_bitsandbytes_NF4",
    },
}


def download_file(url, dest, description=""):
    if dest.exists():
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"  [{description}] Ya existe: {dest.name} ({size_mb:.1f} MB)")
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Descargando {description}... ({dest.name})")

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))

        with open(dest, "wb") as f, tqdm(
            desc=description,
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))

        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"  Completado: {dest.name} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"  ERROR descargando {description}: {e}")
        if dest.exists():
            dest.unlink()
        return False


def install_plugin(name, info):
    dest = info["path"]
    if dest.exists():
        print(f"  [{name}] Plugin ya instalado en {dest}")
        return True

    print(f"  Instalando plugin {name} desde {info['repo']}...")
    try:
        import subprocess

        result = subprocess.run(
            ["git", "clone", info["repo"], str(dest)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr}")
            return False
        print(f"  Plugin {name} instalado correctamente")
        return True
    except Exception as e:
        print(f"  ERROR instalando plugin {name}: {e}")
        return False
    return True


def main():
    print("=" * 60)
    print("  Descargador de modelos para ComfyUI")
    print("=" * 60)

    print("\nDescargando modelos...")
    for key, cfg in MODELS.items():
        success = download_file(cfg["url"], cfg["path"], description=key)
        if not success:
            print(f"  [!] {key}: fallo en descarga")

    print("\nInstalando plugins necesarios...")
    for name, cfg in PLUGINS.items():
        install_plugin(name, cfg)

    print("\n" + "=" * 60)
    print("  Resumen:")
    for key, cfg in MODELS.items():
        exists = cfg["path"].exists()
        status = "OK" if exists else "FALTANTE"
        print(f"    {key:15s} -> {status}")
    for name in PLUGINS:
        exists = PLUGINS[name]["path"].exists()
        status = "OK" if exists else "FALTANTE"
        print(f"    plugin/{name:15s} -> {status}")
    print("=" * 60)


if __name__ == "__main__":
    main()