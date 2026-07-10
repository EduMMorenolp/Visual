FROM pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime

LABEL description="ComfyUI - AI Image Generation (SDXL + Blackwell)"
LABEL version="4.1"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    wget \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN git lfs install

RUN git clone https://github.com/comfyanonymous/ComfyUI.git . \
    && git checkout master

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        insightface \
        onnxruntime-gpu \
        torchsde \
    && pip install --no-cache-dir "kornia==0.6.12" --no-deps \
    && pip install --no-cache-dir "kornia>=0.6,<0.7" \
    && pip uninstall -y kornia_rs 2>/dev/null || true

RUN mkdir -p /app/models/checkpoints \
    /app/models/loras \
    /app/models/vae \
    /app/models/upscale_models \
    /app/output \
    /app/input \
    /app/custom_nodes

COPY workflows/ /app/workflows/
COPY scripts/ /app/scripts/

EXPOSE 8188

ENV COMFYUI_ARGS="--listen 0.0.0.0 --port 8188 --normalvram --force-fp16"
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8188/ || exit 1

CMD ["sh", "-c", "python main.py $COMFYUI_ARGS"]
