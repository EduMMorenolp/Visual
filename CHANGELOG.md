# Changelog

Todas las modificaciones notables de este proyecto se documentarán aquí.

## [Unreleased]

### v3.1.0 - Frontend web para generación de imágenes

- **Added**: Frontend web con FastAPI + Jinja2 para generar imágenes desde el navegador. Interfaz con formulario de prompt, prompt negativo, selección de modelo (SDXL/FLUX), seed, steps, CFG scale y resolución. Incluye visualización de la imagen generada, descarga directa y copia de prompt. Proxy automático a la API de ComfyUI. [2026-07-09]
  * **Files (Archivos)**: `frontend/app.py`, `frontend/templates/index.html`, `frontend/static/style.css`, `frontend/requirements.txt`, `frontend/Dockerfile`. [2026-07-09]

- **Added**: Servicio `frontend` en Docker Compose. Construye desde `frontend/Dockerfile`, expone el puerto 8080, depende del healthcheck de ComfyUI, se comunica internamente via `COMFYUI_URL=http://comfyui:8188`. [2026-07-09]
  * **Files (Archivos)**: `docker-compose.yml` (servicio frontend agregado). [2026-07-09]

- **Added**: Variable `FRONTEND_PORT` en `.env.example` para configurar el puerto del frontend. [2026-07-09]
  * **Files (Archivos)**: `.env.example`. [2026-07-09]

### v3.0.0 - Configuración inicial del proyecto

### v3.0.0 - Configuración inicial del proyecto

- **Added**: Dockerfile con imagen `nvidia/cuda:12.2.0-runtime-ubuntu22.04` + Python 3.11 para compatibilidad con GPU NVIDIA. Se agregó instalación de dependencias del sistema (git, ffmpeg, librerías gráficas), clonación de ComfyUI, instalación de dependencias Python (torch, torchsde, insightface, onnxruntime-gpu), creación de directorios de modelos/salida/input, y auto-descarga del modelo SDXL durante el build. [2026-07-09]
  * **Files (Archivos)**: `Dockerfile` (48 líneas). [2026-07-09]

- **Added**: Orquestación Docker Compose con GPU passthrough. Se definió el servicio `comfyui-sdxl` con montaje de volúmenes para checkpoints, LORAs, VAEs, upscale_models, output, input y custom_nodes. Se expuso el puerto 8188 y se configuró healthcheck. [2026-07-09]
  * **Files (Archivos)**: `docker-compose.yml` (36 líneas). [2026-07-09]

- **Added**: Sistema de configuración por entorno con archivo `.env` y template `.env.example`. Variables documentadas: `COMFYUI_PORT`, `COMFYUI_ARGS` (con explicación de opciones `--normalvram`, `--lowvram`, `--force-fp16`, `--cpu`), `SDXL_MODEL` y `FLUX_MODEL`. [2026-07-09]
  * **Files (Archivos)**: `.env`, `.env.example`. [2026-07-09]

- **Added**: Script `download_models.py` para descarga de modelos SDXL desde HuggingFace (juggernautXL_v8Rundiffusion.safetensors, ~7 GB) y FLUX (flux1-dev-bnb-nf4-v2.safetensors, ~12 GB). Soporte para reanudación (skip si el archivo ya existe), barra de progreso con tqdm, e instalación del plugin `ComfyUI_bitsandbytes_NF4` para FLUX. [2026-07-09]
  * **Files (Archivos)**: `scripts/download_models.py` (124 líneas). [2026-07-09]

- **Added**: Script `generate.py` para generación de imágenes vía API REST de ComfyUI. Soporta prompts positivos/negativos, selección de modelo (sdxl/flux), seed, steps, width/height, cfg_scale. Inyecta prompts en el workflow JSON, envía a `/prompt`, espera resultado vía `/history` y descarga la imagen. [2026-07-09]
  * **Files (Archivos)**: `scripts/generate.py` (185 líneas). [2026-07-09]

- **Added**: Workflows JSON para SDXL (`workflow_sdxl.json`) y FLUX (`workflow_flux_nf4.json`). Cada uno define nodos: CheckpointLoader, CLIPTextEncode (x2), EmptyLatentImage, KSampler, VAEDecode, SaveImage. SDXL usa euler/30 steps/cfg 7, FLUX usa euler/28 steps/cfg 1, ambos en 1024x1024. [2026-07-09]
  * **Files (Archivos)**: `workflows/workflow_sdxl.json`, `workflows/workflow_flux_nf4.json`. [2026-07-09]

- **Fixed**: Error `Fatal Python error: Illegal instruction` al usar `nvidia/cuda:12.2.0-runtime-ubuntu22.04` como imagen base. Causado por incompatibilidad entre Torch y la libc de Ubuntu 22.04 no-slim. [2026-07-09]
  **Problema**: La imagen `nvidia/cuda:12.2.0-runtime-ubuntu22.04` no incluye los paquetes necesarios para Torch, generando un `Illegal instruction` al cargar extensiones nativas.
  **Solución**: Se cambió a `python:3.11-slim` como base y se agregó `nvidia-cuda-toolkit` desde apt. Posteriormente se revirtió a `nvidia/cuda:12.2.0-runtime-ubuntu22.04` + Python 3.11 desde apt porque `python:3.11-slim` usa Debian Trixie que no tiene `libgl1-mesa-glx` ni `nvidia-cuda-toolkit`.
  * **Files (Archivos)**: `Dockerfile` (4 versiones). [2026-07-09]

- **Fixed**: Conflicto de nombre de contenedor zombie en Docker Desktop. El contenedor `comfyui` quedó en estado fantasma después de un build interrumpido, bloqueando el puerto 8188. Se resolvió reiniciando Docker Desktop y eliminando el contenedor huérfano. [2026-07-09]
  * **Files (Archivos)**: `docker-compose.yml` (cambio temporal de `container_name` a `comfyui-sdxl`). [2026-07-09]

- **Changed**: Optimización del build Docker para evitar redescarga del modelo SDXL. Se agregó `COPY models/checkpoints/ /app/models/checkpoints/` antes del `RUN python3 /app/scripts/download_models.py` para que el script detecte el modelo ya existente y lo salte. [2026-07-09]
  * **Files (Archivos)**: `Dockerfile` (línea 49). [2026-07-09]

- **Added**: Documentación del proyecto con `README.md` y `AGENTS.md`. README incluye requisitos, estructura, uso rápido, configuración, comandos útiles, solución de problemas y tabla de modelos. AGENTS.md incluye stack, comandos, estructura, convenciones y notas para el asistente AI. [2026-07-09]
  * **Files (Archivos)**: `README.md`, `AGENTS.md`. [2026-07-09]

- **Added**: Archivo `.gitignore` excluyendo modelos `.safetensors`, directorios `output/`, `input/`, `custom_nodes/`, `.env`, cachés de Python y archivos de OS. [2026-07-09]
  * **Files (Archivos)**: `.gitignore`. [2026-07-09]