"""Gross code memory experiment, issue #44 settings.

Usage: RELAY_DIR=path/to/relay python run.py runs/relay_bp5_X.json
Writes <config stem>_result.json next to the config.
"""
import json
import math
import os
import platform
import sys
import time
from importlib.metadata import version
from pathlib import Path

import sinter
from relay_bp.stim import sinter_decoders

sys.path.append(os.path.join(os.environ.get("RELAY_DIR", "relay"), "tests"))
from testdata import filter_detectors_by_basis, get_test_circuit


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def main(config_path):
    config_path = Path(config_path)
    cfg = json.loads(config_path.read_text())
    d = cfg["decoder"]
    decoders = sinter_decoders(
        gamma0=d["gamma0"],
        pre_iter=d["pre_iter"],
        num_sets=d["num_sets"],
        set_max_iter=d["set_max_iter"],
        gamma_dist_interval=tuple(d["gamma_dist_interval"]),
        stop_nconv=d["stop_nconv"],
    )
    circuit = get_test_circuit(
        circuit=cfg["circuit"],
        distance=cfg["distance"],
        rounds=cfg["rounds"],
        error_rate=cfg["error_rate"],
    )
    circuit = filter_detectors_by_basis(circuit, cfg["basis"])
    task = sinter.Task(
        circuit=circuit,
        decoder="relay-bp",
        collection_options=sinter.CollectionOptions(max_shots=cfg["shots"]),
    )
    start = time.time()
    (out,) = sinter.collect(
        tasks=[task], num_workers=cfg["num_workers"], custom_decoders=decoders
    )
    seconds = time.time() - start

    lo, hi = wilson(out.errors, out.shots)
    ref = cfg["reference"]
    rlo, rhi = wilson(ref["errors"], ref["shots"])
    result = {
        "shots": out.shots,
        "errors": out.errors,
        "ler": out.errors / out.shots,
        "ci95_wilson": [lo, hi],
        "reference": {**ref, "ler": ref["errors"] / ref["shots"], "ci95_wilson": [rlo, rhi]},
        "seconds": seconds,
        "versions": {
            p: version(p) for p in ("relay-bp", "stim", "sinter", "numpy", "scipy")
        }
        | {"python": platform.python_version()},
        "machine": platform.platform(),
        "cpu_count": os.cpu_count(),
        "seed": "not controllable: sinter.collect exposes no seed",
    }
    out_path = config_path.with_name(config_path.stem + "_result.json")
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
