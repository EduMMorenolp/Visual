# ComfyUI - Generación de Imágenes con IA

ComfyUI envuelto en Docker con aceleración GPU NVIDIA para generación de imágenes vía SDXL.

## Requisitos

- Docker Desktop con WSL2 backend
- NVIDIA GPU con drivers recientes
- NVIDIA Container Toolkit (instalado con Docker Desktop)

## Estructura del proyecto

```
├── Dockerfile                  # Imagen con CUDA + ComfyUI + auto-descarga de modelos
├── docker-compose.yml          # Orquestación con GPU passthrough
├── .env                        # Variables de entorno (puerto, args, modelo)
├── models/
│   └── checkpoints/            # Modelos SDXL descargados automáticamente al build
├── workflows/
│   ├── workflow_sdxl.json      # Workflow para SDXL
│   └── workflow_flux_nf4.json  # Workflow para FLUX (no descargado por defecto)
├── scripts/
│   ├── generate.py             # Script Python para generar imágenes vía API
│   └── download_models.py      # Descarga modelos SDXL y FLUX
├── input/                      # Imágenes de entrada (img2img)
├── output/                     # Imágenes generadas
├── custom_nodes/               # Plugins de ComfyUI
├── README.md
└── AGENTS.md
```

## Uso rápido

### 1. Construir y levantar

```bash
docker compose up -d --build
```

Esto construye la imagen, descarga el modelo SDXL (~7 GB) y levanta ComfyUI en `http://localhost:8188`.

### 2. Generar imagen

Opción A — Script Python (recomendado):

```bash
# Si tienes Python local con requests + Pillow:
pip install requests Pillow
python scripts/generate.py --prompt "astronaut riding a horse" -o output/imagen.png
```

Opción B - Desde dentro del contenedor:

```bash
docker exec comfyui python3 /app/scripts/generate.py \
    --prompt "astronaut riding a horse, cinematic lighting" \
    -o /app/output/astronaut_horse.png
```

Opción C - API directa (ejemplo con curl):

```bash
curl.exe -X POST http://localhost:8188/prompt ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\": {\"3\": {\"class_type\": \"CLIPTextEncode\", \"inputs\": {\"text\": \"astronaut riding a horse\", \"clip\": [\"1\", 1]}}, \"4\": {\"class_type\": \"EmptyLatentImage\", \"inputs\": {\"width\": 1024, \"height\": 1024, \"batch_size\": 1}}, \"5\": {\"class_type\": \"KSampler\", \"inputs\": {\"seed\": 0, \"steps\": 30, \"cfg\": 7, \"sampler_name\": \"euler\", \"scheduler\": \"normal\", \"denoise\": 1, \"model\": [\"1\", 0], \"positive\": [\"3\", 0], \"negative\": [\"2\", 0], \"latent_image\": [\"4\", 0]}}, \"6\": {\"class_type\": \"VAEDecode\", \"inputs\": {\"samples\": [\"5\", 0], \"vae\": [\"1\", 2]}}, \"7\": {\"class_type\": \"SaveImage\", \"inputs\": {\"filename_prefix\": \"ComfyUI\", \"images\": [\"6\", 0]}}}}"
```

### 3. Ver resultados

Las imágenes se guardan en `output/`. También puedes abrir `http://localhost:8188` en el navegador para usar la interfaz web.

## Variables de entorno (.env)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `COMFYUI_PORT` | `8188` | Puerto del servicio |
| `COMFYUI_ARGS` | `--listen 0.0.0.0 --port 8188 --normalvram --force-fp16` | Args de ComfyUI |
| `SDXL_MODEL` | `juggernautXL_v8Rundiffusion.safetensors` | Nombre del checkpoint SDXL |

## Solución de problemas

- **GPU no detectada**: `docker info` debe mostrar `nvidia` en la lista de runtimes
- **VRAM insuficiente**: Cambiar `--normalvram` a `--lowvram` en `COMFYUI_ARGS`
- **Error de conexión**: Esperar a que el healthcheck pase (`docker compose ps`)
- **Modelo no descargado**: Revisar logs con `docker compose logs comfyui | findstr download`

## Modelos disponibles

| Modelo | Tamaño | VRAM recomendada | workflow |
|--------|--------|-------------------|----------|
| SDXL (Juggernaut XL v8) | ~7 GB | 6-8 GB | `workflow_sdxl.json` |
| FLUX.1 dev NF4 | ~12 GB | 8-12 GB | `workflow_flux_nf4.json` |

Para descargar FLUX manualmente: `python3 /app/scripts/download_models.py` dentro del contenedor.