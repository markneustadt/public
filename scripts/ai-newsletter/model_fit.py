#!/usr/bin/env python3
"""Compute model-fit verdicts for the newsletter's machine table.

Usage: model_fit.py <params_billions> <quant_bits> [context_tokens] [n_layers_total] [n_layers_gpu]
  e.g. model_fit.py 70 4 8192          -> pure-CPU-style run of 70B Q4
       model_fit.py 120 4 8192 80 40   -> 120B MoE, 40 of 80 layers offloaded to RAM

Weights = params_B * 1e9 * bits/8 * 1.05 (overhead). KV cache ~ params-based heuristic.
Speed estimate (decode, tok/s) ~= bandwidth_GBs / bytes_touched_per_token * 0.75,
where bytes_touched_per_token = bytes of weights resident in the fast memory.
Prints JSON verdicts for every machine in config.json.
"""
import json, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))


def fit(weights_bytes, kv_bytes, m, n_layers_total=0, n_layers_gpu=0):
    gb = 1e9
    vram, ram, bw = m["vram_gb"] * gb, m["sys_ram_gb"] * gb, m["bandwidth_gbs"]
    if m.get("unified"):
        need = weights_bytes + kv_bytes
        fast_bytes = need  # everything shares the unified pool
        fits = need <= vram * 0.90
        ram_note = ""
    elif n_layers_gpu and n_layers_total and n_layers_gpu < n_layers_total:
        gpu_w = weights_bytes * (n_layers_gpu / n_layers_total)
        cpu_w = weights_bytes - gpu_w
        fits = gpu_w + kv_bytes <= vram * 0.90 and cpu_w <= ram * 0.6
        fast_bytes = gpu_w + kv_bytes
        ram_note = "partial offload"
    else:
        fits_full = weights_bytes + kv_bytes <= vram * 0.90
        fits = fits_full or (weights_bytes <= (vram + ram) * 0.7)
        fast_bytes = (weights_bytes + kv_bytes) if fits_full else weights_bytes * (vram * 0.7 / max(weights_bytes, 1)) + kv_bytes
        if not fits_full:
            bw = min(bw, 60)  # DDR5-60ish system RAM is the pipe once weights spill out of VRAM
        ram_note = "" if fits_full else "GPU+RAM offload (slow)"
    tok_s = (bw * 1e9 / max(fast_bytes, 1)) * 0.75 if fits else 0
    headroom = vram - (weights_bytes + kv_bytes) / gb if m.get("unified") is False else vram * 0.9 - (weights_bytes + kv_bytes) / gb
    return {
        "fits": fits,
        "weight_gb": round(weights_bytes / gb, 1),
        "total_gb": round((weights_bytes + kv_bytes) / gb, 1),
        "est_tok_s": round(min(tok_s, 120), 1) if fits else 0,
        "note": ram_note,
        "verdict": ("YES" if fits and tok_s >= 8 else "MARGINAL" if fits else "NO"),
    }


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: model_fit.py <params_B> <quant_bits> [ctx] [layers_total] [layers_on_gpu]")
    p = float(sys.argv[1]) * 1e9
    bits = float(sys.argv[2])
    ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 8192
    lt = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    lg = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    weights = p * bits / 8 * 1.05
    # crude KV: ~0.02 GB per 1k tokens per 10B params, floored
    kv = max(0.5, (p / 1e9) * 0.02 * (ctx / 1024)) * 1e9
    with open(os.path.join(DIR, "config.json")) as f:
        cfg = json.load(f)
    out = {"params_B": p / 1e9, "quant_bits": bits, "context": ctx, "machines": {}}
    for name, m in cfg["machines"].items():
        out["machines"][name] = fit(weights, kv, m, lt, lg)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
