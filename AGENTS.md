# AGENTS.md - Instrucciones para el asistente

## Proyecto
ComfyUI + Docker + GPU para generación de imágenes con IA. Modelo principal: SDXL (Juggernaut XL v8).

## Stack

- **ComfyUI**: Backend de generación de imágenes
- **Frontend**: Vite + Vanilla JS (puerto 8080, se ejecuta local en Windows)
- **Docker**: Contenedor CUDA 12.8 + Ubuntu 22.04
- **GPU**: NVIDIA RTX 5050 (8GB VRAM, sm_120)
- **Python 3.11**: Dentro del contenedor (no hay Python en Windows host)
- **API REST**: ComfyUI expone endpoints en puerto 8188

## Comandos útiles

```bash
# Configurar entorno
cp .env.example .env

# Construir y levantar ComfyUI
docker compose up -d --build visual-comfyui

# Ver logs de ComfyUI
docker compose logs -f visual-comfyui-1

# Iniciar frontend Vite (local, NO docker)
cd frontend && npm run dev

# Ejecutar comando dentro del contenedor
docker exec visual-comfyui-1 python3 /app/scripts/generate.py [args]

# Ver estado
docker compose ps

# Detener
docker compose down
```

## Estructura

```
Dockerfile                    # Imagen con CUDA 12.8 + PyTorch 2.7 + descarga modelo al build
docker-compose.yml            # GPU passthrough via nvidia runtime
.env.example                  # Template de configuración (copiar a .env)
.env                          # Config: puerto, args, modelo (NO versionar)
models/checkpoints/           # Modelos .safetensors (~7 GB SDXL)
workflows/                    # Workflows JSON de ComfyUI
frontend/                     # Frontend Vite (Vanilla JS)
  index.html                  #   HTML principal
  vite.config.js              #   Proxy a ComfyUI en localhost:8188
  src/main.js                 #   Lógica JS (inyección workflow, polling)
  src/style.css               #   Estilos
  package.json                #   Dependencias (solo Vite)
  public/workflows/           #   Copia de workflows para dev
scripts/generate.py           # Script para generar desde CLI
scripts/download_models.py    # Descarga modelos SDXL/FLUX
output/                       # Imágenes generadas
input/                        # Inputs para img2img
custom_nodes/                 # Plugins
```

## Convenciones

- Todos los comandos Docker se ejecutan desde la raíz del proyecto
- Las imágenes generadas se guardan en `output/`
- No hay Python en Windows host; todo corre dentro del contenedor
- Usar `--normalvram --force-fp16` por defecto (RTX 5050 8GB)
- Si hay OOM, cambiar a `--lowvram`
- Con Blackwell (sm_120), ComfyUI puede autoajustar a `LOW_VRAM` en primera generación
- El `.env` y los `.safetensors` están en `.gitignore`

## Workflows

- `workflow_sdxl.json`: Modelo SDXL, sampler euler, 30 steps, cfg 7, 1024x1024
- `workflow_flux_nf4.json`: Modelo FLUX, sampler euler, 28 steps, cfg 1, 1024x1024

## Frontend web

- URL: `http://localhost:8080`
- Proxy automático a ComfyUI API (no requiere configurar CORS)
- Parámetros: prompt, negativo, modelo, seed, steps, cfg, resolución
- Descarga directa de imagen y copia de prompt al portapapeles

## Notas

- El modelo SDXL se descarga automáticamente durante el build de Docker
- Para FLUX, ejecutar `python3 /app/scripts/download_models.py` manualmente dentro del contenedor
- La primera generación puede tardar ~3 min (carga del modelo a VRAM + compilación de kernels Blackwell)
- No modificar `docker-compose.yml` sin verificar compatibilidad con GPU en Windows
- PyTorch ≥2.7.0 + CUDA ≥12.8 requerido para RTX 5050 (Blackwell sm_120)