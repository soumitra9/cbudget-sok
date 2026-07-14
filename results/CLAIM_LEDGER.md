# Claim ledger (Stage 7)

| Claim | Evidence | Label |
|---|---|---|
| Token populations have different recurrence behavior | E0 anatomy + formal model | empirically-demonstrated + analytically-illustrated |
| RTK and compaction interact non-additively | E1 mock runs (244 trajectories) | conditional (confirmatory pending GPU MDE gate) |
| RTK and CoD interact non-additively or multiplicatively | E1b mock runs | conditional |
| Single-shot GT metrics understate session effects under replay | C4 simulation | analytically-illustrated |
| Replay in implemented agent environment | E0/E1b traces | empirically-demonstrated (mock backend) |
| Published metrics not commensurable | C2 table from extraction sheet | documented |
| Other taxonomy interactions | interaction registry | untested |

## Paper wiring

See [PAPER_WIRE.md](PAPER_WIRE.md).

## GPU note

Stage 2 live validation requires RunPod API credentials and an A40 pod with vLLM. Use:

```bash
uv run python -m scripts.run_stage2_gpu_integration
```

after `launch_vllm.sh` and SSH port-forward to `:8000`.
