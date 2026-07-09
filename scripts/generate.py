import json
import time
import uuid
import requests
from pathlib import Path
from io import BytesIO
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
WORKFLOWS_DIR = BASE_DIR / "workflows"

COMFYUI_URL = "http://localhost:8188"

WORKFLOW_FILES = {
    "sdxl": WORKFLOWS_DIR / "workflow_sdxl.json",
    "flux": WORKFLOWS_DIR / "workflow_flux_nf4.json",
}


def generate_image(
    prompt: str,
    negative_prompt: str = "",
    model: str = "sdxl",
    seed: int = -1,
    steps: int = None,
    width: int = 1024,
    height: int = 1024,
    cfg_scale: float = 7.0,
    comfy_url: str = COMFYUI_URL,
) -> list[Image.Image]:
    workflow_file = WORKFLOW_FILES.get(model)
    if not workflow_file:
        raise ValueError(f"Modelo no soportado: {model}. Usa: {list(WORKFLOW_FILES.keys())}")

    if not workflow_file.exists():
        raise FileNotFoundError(f"Workflow no encontrado: {workflow_file}")

    with open(workflow_file) as f:
        workflow = json.load(f)

    for node_id, node in workflow.items():
        if node["class_type"] == "CLIPTextEncode":
            clip_from = node["inputs"].get("clip", [None, 0])[0]
            parent = workflow.get(str(clip_from), {})
            parent_type = parent.get("class_type", "")

            if "text" not in node["inputs"]:
                continue

            is_negative = False
            node_title = node.get("_meta", {}).get("title", "")
            if "negative" in node_title.lower():
                is_negative = True

            if is_negative:
                continue
            node["inputs"]["text"] = prompt

        elif node["class_type"] == "EmptyLatentImage":
            node["inputs"]["width"] = width
            node["inputs"]["height"] = height

        elif node["class_type"] == "KSampler":
            if steps is not None:
                node["inputs"]["steps"] = steps
            if seed >= 0:
                node["inputs"]["seed"] = seed
            if model == "flux":
                node["inputs"]["cfg"] = 1
            else:
                node["inputs"]["cfg"] = cfg_scale

    negative_set = False
    for node_id, node in workflow.items():
        if node["class_type"] == "CLIPTextEncode" and "text" in node["inputs"]:
            node_title = node.get("_meta", {}).get("title", "")
            if "negative" in node_title.lower() or node.get("inputs", {}).get("text", "") == "":
                if not negative_set:
                    node["inputs"]["text"] = negative_prompt
                    negative_set = True

    client_id = str(uuid.uuid4())
    payload = {"prompt": workflow, "client_id": client_id}

    try:
        r = requests.post(f"{comfy_url}/prompt", json=payload, timeout=60)
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"No se pudo conectar a ComfyUI en {comfy_url}. "
            "¿Está corriendo el contenedor?"
        )

    result = r.json()
    if "prompt_id" not in result:
        errors = result.get("node_errors", result.get("error", "Unknown error"))
        raise RuntimeError(f"Error en workflow: {errors}")

    prompt_id = result["prompt_id"]

    while True:
        try:
            hist = requests.get(f"{comfy_url}/history/{prompt_id}", timeout=10)
            hist.raise_for_status()
            data = hist.json()
            if prompt_id in data and "outputs" in data[prompt_id]:
                break
        except requests.exceptions.RequestException:
            raise RuntimeError("Error consultando historial")
        time.sleep(0.5)

    images = []
    outputs = data[prompt_id]["outputs"]
    for node_id in outputs:
        node_output = outputs[node_id]
        for img_info in node_output.get("images", []):
            try:
                img_r = requests.get(
                    f"{comfy_url}/view",
                    params={
                        "filename": img_info["filename"],
                        "subfolder": img_info.get("subfolder", ""),
                        "type": img_info.get("type", "output"),
                    },
                    timeout=30,
                )
                img_r.raise_for_status()
                images.append(Image.open(BytesIO(img_r.content)))
            except Exception as e:
                print(f"  Error descargando imagen {img_info['filename']}: {e}")

    return images


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generar imagen via ComfyUI")
    parser.add_argument("--prompt", "-p", required=True, help="Prompt de texto")
    parser.add_argument("--negative", "-n", default="", help="Prompt negativo")
    parser.add_argument("--model", "-m", default="sdxl", choices=["sdxl", "flux"], help="Modelo a usar")
    parser.add_argument("--seed", "-s", type=int, default=-1, help="Semilla (-1 = aleatoria)")
    parser.add_argument("--steps", type=int, default=None, help="Pasos de sampling")
    parser.add_argument("--width", type=int, default=1024, help="Ancho")
    parser.add_argument("--height", type=int, default=1024, help="Alto")
    parser.add_argument("--cfg", type=float, default=7.0, help="CFG scale (solo SDXL)")
    parser.add_argument("--output", "-o", default=None, help="Archivo de salida")
    parser.add_argument("--url", default=COMFYUI_URL, help="URL de ComfyUI")

    args = parser.parse_args()

    print(f"Generando con modelo '{args.model}'...")
    print(f"  Prompt: {args.prompt}")
    if args.negative:
        print(f"  Negativo: {args.negative}")

    start = time.time()
    images = generate_image(
        prompt=args.prompt,
        negative_prompt=args.negative,
        model=args.model,
        seed=args.seed,
        steps=args.steps,
        width=args.width,
        height=args.height,
        cfg_scale=args.cfg,
        comfy_url=args.url,
    )
    elapsed = time.time() - start

    if not images:
        print("ERROR: No se generaron imagenes")
        sys.exit(1)

    output_path = args.output
    if output_path is None:
        output_dir = BASE_DIR / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = str(output_dir / f"{args.model}_{timestamp}.png")

    images[0].save(output_path)
    print(f"  Completado en {elapsed:.1f}s")
    print(f"  Imagen guardada: {output_path}")