FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

LABEL description="ComfyUI - AI Image Generation (SDXL)"
LABEL version="3.0"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    python3.11-dev \
    git \
    git-lfs \
    wget \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

RUN git lfs install

RUN git clone https://github.com/comfyanonymous/ComfyUI.git . \
    && git checkout master

RUN pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir \
        insightface \
        onnxruntime-gpu \
        torchsde

RUN mkdir -p /app/models/checkpoints \
    /app/models/loras \
    /app/models/vae \
    /app/models/upscale_models \
    /app/output \
    /app/input \
    /app/custom_nodes

RUN pip3 install requests Pillow tqdm

COPY scripts/download_models.py /app/scripts/download_models.py
COPY models/checkpoints/ /app/models/checkpoints/
RUN python3 /app/scripts/download_models.py

COPY workflows/ /app/workflows/
COPY scripts/generate.py /app/scripts/generate.py

EXPOSE 8188

ENV COMFYUI_ARGS="--listen 0.0.0.0 --port 8188 --normalvram --force-fp16"
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8188/ || exit 1

CMD ["sh", "-c", "python3 main.py $COMFYUI_ARGS"]