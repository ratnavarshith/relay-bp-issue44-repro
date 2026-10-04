"""Collect runs/*_result.json into results.csv and print the per-cycle LER.

Usage: python summarize.py
"""
import csv
import json
import math
from pathlib import Path

ROUNDS = 12


def per_cycle(p):
    return 1 - (1 - p) ** (1 / ROUNDS)


rows = []
for path in sorted(Path("runs").glob("*_result.json")):
    r = json.loads(path.read_text())
    rows.append(
        {
            "run": path.name.removesuffix("_result.json"),
            "shots": r["shots"],
            "errors": r["errors"],
            "ler_per_shot": r["ler"],
            "ci95_low": r["ci95_wilson"][0],
            "ci95_high": r["ci95_wilson"][1],
            "seconds": round(r["seconds"], 1),
        }
    )

with open("results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

by_run = {row["run"]: row for row in rows}
x = by_run["relay_bp5_X"]
zs = [row for name, row in by_run.items() if name.startswith("relay_bp5_Z")]
nx, nz = x["shots"], sum(row["shots"] for row in zs)
px, pz = x["errors"] / nx, sum(row["errors"] for row in zs) / nz
p = 1 - (1 - px) * (1 - pz)
sd = math.sqrt(px * (1 - px) / nx + pz * (1 - pz) / nz)
print(f"p_X = {px:.4e}, p_Z = {pz:.4e} ({len(zs)} Z runs pooled)")
print(f"X or Z per shot: {p:.4e}")
print(
    f"per cycle: {per_cycle(p):.3e}  "
    f"95% CI [{per_cycle(p - 1.96 * sd):.3e}, {per_cycle(p + 1.96 * sd):.3e}]"
)
