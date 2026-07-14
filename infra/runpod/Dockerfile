# Optional pre-baked image: build once, push to a registry, then set POD_IMAGE in pins.env
# or RUNPOD_IMAGE when creating pods. Cuts fresh-pod setup from ~15min to ~2min (cbudget clone + rtk only).
#
#   docker build -t YOUR_USER/cbudget-sok-vllm:latest -f infra/runpod/Dockerfile .
#   docker push YOUR_USER/cbudget-sok-vllm:latest
#
FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

ENV DEBIAN_FRONTEND=noninteractive
ENV VLLM_ENV=/root/vllm_env
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

RUN apt-get update -qq && apt-get install -y -qq git curl rsync build-essential && rm -rf /var/lib/apt/lists/*

# uv for cbudget harness
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# rust for RTK
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# vLLM: inherit system torch 2.8+cu128; never install default vllm wheel (cu129/cu130)
RUN python3 -m venv /root/vllm_env --system-site-packages && \
    /root/vllm_env/bin/pip install --no-cache-dir \
      "vllm==0.8.5.post1" \
      "transformers>=4.45,<4.53"

# Pre-build RTK at pinned commit
ARG RTK_PINNED_COMMIT=5d32d0736f686b69d1e8b9dc45c007d4eb77a0a2
RUN git clone https://github.com/rtk-ai/rtk.git /opt/rtk && \
    git -C /opt/rtk checkout ${RTK_PINNED_COMMIT} && \
    cd /opt/rtk && cargo build --release

# Seed script copies prebuilt rtk into cbudget checkout on first pod_setup
COPY infra/runpod/pins.env /opt/cbudget-pins.env
COPY infra/runpod/pod_setup.sh /opt/pod_setup.sh
