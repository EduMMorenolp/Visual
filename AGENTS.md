# AGENTS.md - Instrucciones para el asistente

## Proyecto
ComfyUI + Docker + GPU para generación de imágenes con IA. Modelo principal: SDXL (Juggernaut XL v8).

## Stack

- **ComfyUI**: Frontend/backend de generación de imágenes
- **Docker**: Contenedor CUDA 12.2 + Ubuntu 22.04
- **GPU**: NVIDIA RTX 5050 (8GB VRAM)
- **Python 3.11**: Dentro del contenedor (no hay Python en Windows host)
- **API REST**: ComfyUI expone endpoints en puerto 8188

## Comandos útiles

```bash
# Construir y levantar
docker compose up -d --build

# Ver logs
docker compose logs -f comfyui

# Ejecutar comando dentro del contenedor
docker exec comfyui python3 /app/scripts/generate.py [args]

# Ver estado
docker compose ps

# Detener
docker compose down
```

## Estructura

```
Dockerfile                    # Imagen con CUDA + auto-descarga modelo al build
docker-compose.yml            # GPU passthrough via nvidia runtime
.env                          # Config: puerto, args, modelo
models/checkpoints/           # Modelos .safetensors (~7 GB SDXL)
workflows/                    # Workflows JSON de ComfyUI
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

## Workflows

- `workflow_sdxl.json`: Modelo SDXL, sampler euler, 30 steps, cfg 7, 1024x1024
- `workflow_flux_nf4.json`: Modelo FLUX, sampler euler, 28 steps, cfg 1, 1024x1024

## Notas

- El modelo SDXL se descarga automáticamente durante el build de Docker
- Para FLUX, ejecutar `python3 /app/scripts/download_models.py` manualmente dentro del contenedor
- La primera generación puede tardar ~1-2 min (carga del modelo a VRAM)
- No modificar `docker-compose.yml` sin verificar compatibilidad con GPU en Windows