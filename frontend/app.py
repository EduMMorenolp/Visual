import os
import json
import uuid
import time
import httpx
from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="ComfyUI Frontend")

BASE_DIR = Path(__file__).resolve().parent
WORKFLOWS_DIR = BASE_DIR.parent / "workflows"

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://comfyui:8188")

WORKFLOW_FILES = {
    "sdxl": WORKFLOWS_DIR / "workflow_sdxl.json",
    "flux": WORKFLOWS_DIR / "workflow_flux_nf4.json",
}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/generate")
async def generate(
    prompt: str = Form(...),
    negative_prompt: str = Form(""),
    model: str = Form("sdxl"),
    seed: int = Form(-1),
    steps: int = Form(None),
    width: int = Form(1024),
    height: int = Form(1024),
    cfg_scale: float = Form(7.0),
):
    workflow_file = WORKFLOW_FILES.get(model)
    if not workflow_file:
        return JSONResponse(
            status_code=400,
            content={"error": f"Modelo no soportado: {model}. Usa: {list(WORKFLOW_FILES.keys())}"},
        )

    if not workflow_file.exists():
        return JSONResponse(
            status_code=400,
            content={"error": f"Workflow no encontrado: {workflow_file}"},
        )

    with open(workflow_file) as f:
        workflow = json.load(f)

    for node_id, node in workflow.items():
        if node["class_type"] == "CLIPTextEncode":
            clip_from = node["inputs"].get("clip", [None, 0])[0]
            parent = workflow.get(str(clip_from), {})
            parent_type = parent.get("class_type", "")

            if "text" not in node["inputs"]:
                continue

            node_title = node.get("_meta", {}).get("title", "")
            if "negative" in node_title.lower():
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
            if node_title.lower().startswith("negative") or node.get("inputs", {}).get("text", "") == "":
                if not negative_set:
                    node["inputs"]["text"] = negative_prompt
                    negative_set = True

    client_id = str(uuid.uuid4())

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow, "client_id": client_id})
            r.raise_for_status()
    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={"error": f"No se pudo conectar a ComfyUI en {COMFYUI_URL}. ¿Está corriendo el contenedor?"},
        )

    result = r.json()
    if "prompt_id" not in result:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error en workflow: {result.get('node_errors', result.get('error', 'Unknown error'))}"},
        )

    prompt_id = result["prompt_id"]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for _ in range(300):
            try:
                hist = await client.get(f"{COMFYUI_URL}/history/{prompt_id}")
                hist.raise_for_status()
                data = hist.json()
                if prompt_id in data and "outputs" in data[prompt_id]:
                    break
            except httpx.RequestError:
                pass
            time.sleep(0.5)
        else:
            return JSONResponse(
                status_code=504,
                content={"error": "Timeout esperando la generación de la imagen"},
            )

    outputs = data[prompt_id]["outputs"]
    images = []
    for node_id in outputs:
        node_output = outputs[node_id]
        for img_info in node_output.get("images", []):
            try:
                img_r = await client.get(
                    f"{COMFYUI_URL}/view",
                    params={
                        "filename": img_info["filename"],
                        "subfolder": img_info.get("subfolder", ""),
                        "type": img_info.get("type", "output"),
                    },
                )
                img_r.raise_for_status()
                images.append({
                    "filename": img_info["filename"],
                    "data": img_r.content,
                    "type": img_r.headers.get("content-type", "image/png"),
                })
            except Exception as e:
                pass

    if not images:
        return JSONResponse(status_code=500, content={"error": "No se generaron imágenes"})

    img = images[0]
    return Response(content=img["data"], media_type=img["type"])


@app.get("/api/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{COMFYUI_URL}/")
            return {"status": "ok", "comfyui": r.status_code}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})
