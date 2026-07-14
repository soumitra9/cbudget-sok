# cbudget — SoK Context Budget experiment harness

End-to-end experiment harness for **SoK: Context as a Budget** (E0, E1, E1b).

## Setup

```bash
uv sync --all-extras
uv run python -m scripts.validate_rtk_semantics
```

## Run locally (mock, no GPU)

```bash
CBUDGET_BACKEND=mock uv run python -m scripts.run_calibration_gate
```

## RunPod (A40 + vLLM)

Uses personal SSH key (`~/.ssh/id_ed25519_personal`), not corporate git keys.

```bash
bash scripts/runpod_create_pod.sh
bash infra/runpod/bootstrap.sh <POD_IP>
bash infra/runpod/launch_vllm.sh configs/models/qwen2.5_7b_instruct.yaml <POD_IP>
export CBUDGET_BACKEND=vllm VLLM_BASE_URL=http://localhost:8000
uv run python -m scripts.run_stage2_gpu_integration
```

RTK is vendored at runtime: `external/rtk/` is built from commit in `external/rtk/PINNED_COMMIT`.

## License

Research code for SoK paper experiments.
