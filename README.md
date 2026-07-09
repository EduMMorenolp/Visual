# ComfyUI - Generación de Imágenes con IA

ComfyUI envuelto en Docker con aceleración GPU NVIDIA para generación de imágenes vía SDXL.

## Requisitos

- Docker Desktop con WSL2 backend
- NVIDIA GPU con drivers recientes
- NVIDIA Container Toolkit (instalado con Docker Desktop)

## Primeros pasos

```bash
# 1. Configurar entorno
cp .env.example .env

# 2. Descargar modelo SDXL (si no está en models/checkpoints/)
# Opción A: build automático (lo descarga durante la construcción)
# Opción B: manual desde https://huggingface.co/RunDiffusion/Juggernaut-XL-v8

# 3. Construir y levantar
docker compose up -d --build

# 4. Verificar que esté corriendo
docker compose ps

# 5. Generar una imagen de prueba
docker exec visual-comfyui-1 python3 /app/scripts/generate.py \
    --prompt "astronaut riding a horse, cinematic lighting" \
    -o /app/output/test.png
```

## Estructura del proyecto

```
├── Dockerfile                  # Imagen con CUDA + ComfyUI
├── docker-compose.yml          # Orquestación con GPU passthrough
├── .env.example                # Template de configuración (copiar a .env)
├── .env                        # Configuración local (NO versionar)
├── .gitignore
├── README.md
├── AGENTS.md                   # Instrucciones para el asistente AI
├── CHANGELOG.md
├── models/
│   └── checkpoints/            # Modelos .safetensors (~7 GB SDXL)
├── workflows/
│   ├── workflow_sdxl.json      # Workflow SDXL (euler, 30 steps, cfg 7, 1024x1024)
│   └── workflow_flux_nf4.json  # Workflow FLUX (euler, 28 steps, cfg 1, 1024x1024)
├── frontend/                   # Servicio frontend web
│   ├── app.py                  #   API FastAPI + proxy a ComfyUI
│   ├── Dockerfile
│   ├── templates/index.html    #   UI
│   └── static/style.css        #   Estilos
├── scripts/
│   ├── generate.py             # Script Python para generar desde CLI
│   └── download_models.py      # Descarga modelos SDXL y FLUX
├── input/                      # Imágenes de entrada (img2img)
├── output/                     # Imágenes generadas
└── custom_nodes/               # Plugins de ComfyUI
```

## Uso

### Construir y levantar

```bash
docker compose up -d --build
```

Esto construye la imagen, copia el modelo SDXL si existe localmente (o lo descarga) y levanta ComfyUI en `http://localhost:8188`.

### Generar imágenes

Opción A — Desde dentro del contenedor (recomendado):

```bash
docker exec visual-comfyui-1 python3 /app/scripts/generate.py \
    --prompt "astronaut riding a horse" \
    -o /app/output/imagen.png
```

Opción B — API directa:

```bash
curl.exe -X POST http://localhost:8188/prompt ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\": {\"3\": {\"class_type\": \"CLIPTextEncode\", \"inputs\": {\"text\": \"astronaut riding a horse\", \"clip\": [\"1\", 1]}}, \"4\": {\"class_type\": \"EmptyLatentImage\", \"inputs\": {\"width\": 1024, \"height\": 1024, \"batch_size\": 1}}, \"5\": {\"class_type\": \"KSampler\", \"inputs\": {\"seed\": 0, \"steps\": 30, \"cfg\": 7, \"sampler_name\": \"euler\", \"scheduler\": \"normal\", \"denoise\": 1, \"model\": [\"1\", 0], \"positive\": [\"3\", 0], \"negative\": [\"2\", 0], \"latent_image\": [\"4\", 0]}}, \"6\": {\"class_type\": \"VAEDecode\", \"inputs\": {\"samples\": [\"5\", 0], \"vae\": [\"1\", 2]}}, \"7\": {\"class_type\": \"SaveImage\", \"inputs\": {\"filename_prefix\": \"ComfyUI\", \"images\": [\"6\", 0]}}}}"
```

### Ver resultados

Las imágenes se guardan en `output/`. También puedes abrir `http://localhost:8188` en el navegador para usar la interfaz web de ComfyUI.

## Configuración

Copia `.env.example` a `.env` y ajusta las variables:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `COMFYUI_PORT` | `8188` | Puerto del servicio |
| `COMFYUI_ARGS` | `--listen 0.0.0.0 --port 8188 --normalvram --force-fp16` | Argumentos de inicio de ComfyUI |
| `COMFYUI_ARGS` (CPU) | `--listen 0.0.0.0 --port 8188 --cpu` | Para ejecutar sin GPU |
| `SDXL_MODEL` | `juggernautXL_v8Rundiffusion.safetensors` | Nombre del checkpoint SDXL |
| `FLUX_MODEL` | `flux1-dev-bnb-nf4-v2.safetensors` | Nombre del checkpoint FLUX |
| `FRONTEND_PORT` | `8080` | Puerto del frontend web |

## Comandos útiles

### Frontend web

El proyecto incluye un frontend web en `http://localhost:8080`:

```bash
docker compose up -d --build  # ya incluye el frontend
# Abrir http://localhost:8080
```

Tiene interfaz moderna con:
- Formulario de prompt con todos los parámetros
- Selección de modelo (SDXL / FLUX)
- Vista previa de la imagen generada
- Descarga directa y copia de prompt
- Indicador de estado de conexión a ComfyUI

## Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f visual-comfyui-1

# Ver logs del frontend
docker compose logs -f frontend

# Ver estado
docker compose ps

# Ejecutar comando dentro del contenedor
docker exec visual-comfyui-1 python3 /app/scripts/generate.py [args]

# Detener
docker compose down

# Reconstruir desde cero (sin caché)
docker compose build --no-cache
docker compose up -d
```

## Solución de problemas

- **GPU no detectada**: `docker info` debe mostrar `nvidia` en la lista de runtimes
- **VRAM insuficiente (OOM)**: Cambiar `--normalvram` a `--lowvram` en `COMFYUI_ARGS`
- **Error de conexión**: Esperar a que el healthcheck pase (`docker compose ps`)
- **Modelo no descargado**: Revisar logs con `docker compose logs | findstr download`
- **Contenedor no arranca**: Ver logs completos con `docker compose logs`

## Modelos disponibles

| Modelo | Tamaño | VRAM recomendada | Workflow | Descarga |
|--------|--------|-------------------|----------|----------|
| SDXL (Juggernaut XL v8) | ~7 GB | 6-8 GB | `workflow_sdxl.json` | Automática al build |
| FLUX.1 dev NF4 | ~12 GB | 8-12 GB | `workflow_flux_nf4.json` | Manual: `python3 /app/scripts/download_models.py` dentro del contenedor |

## Notas para desarrolladores

- Todos los comandos Docker se ejecutan desde la raíz del proyecto
- No hay Python en Windows host; todo corre dentro del contenedor
- Las imágenes generadas se guardan en `output/`
- La primera generación puede tardar ~1-2 min (carga del modelo a VRAM)
- Los modelos `.safetensors` están en `.gitignore` por su tamaño
- El `.env` contiene configuración local sensible (no versionar)