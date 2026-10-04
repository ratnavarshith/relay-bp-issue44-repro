# relay-bp issue #44 reproduction

Gross code [[144,12,12]] memory experiment with the Relay-BP-5 settings from
[trmue/relay#44](https://github.com/trmue/relay/issues/44), run on both memory-X and memory-Z.

## What was run

- Circuits: `bicycle_bivariate_144_12_12_memory_{X,Z}`, distance 12, 12 rounds, p = 0.003,
  uniform circuit noise, from `relay/tests/testdata`. Detectors filtered to the memory basis
  with `filter_detectors_by_basis` (936 detectors, 12 observables).
- Decoder: relay-bp sinter decoder, gamma0 = 0.125, gamma interval [-0.24, 0.66],
  pre_iter = 80, num_sets = 600 (601 legs), set_max_iter = 60, stop_nconv = 5.
- 300,000 shots per run, 10 sinter workers. memory-Z was run twice with an identical config
  (`relay_bp5_Z`, then `relay_bp5_Z_rerun`) because the first run came out low.
- relay-bp 0.2.2 built from main at d185194ba0cb4101ced4340d82b2ee6d42f225f0
  (`maturin develop --release --extras stim`), stim 1.16.0, sinter 1.16.0, numpy 2.2.6,
  scipy 1.17.1, Python 3.11.9, Windows 11, Intel i5-13500HX (20 threads), 16 GB RAM.
- No sampling seed: `sinter.collect` does not expose one. The decoder's gamma RNG uses its
  default seed of 0.

Each config in `runs/` has its result next to it (`*_result.json`). `calib_*` are 2,000-shot
throughput checks with the same settings.

## Results

| Run | Shots | Errors | LER per shot | 95% CI (Wilson) |
| --- | --- | --- | --- | --- |
| memory-X | 300,000 | 118 | 3.93e-4 | [3.28e-4, 4.71e-4] |
| memory-Z, first run | 300,000 | 87 | 2.90e-4 | [2.35e-4, 3.58e-4] |
| memory-Z, rerun | 300,000 | 115 | 3.83e-4 | [3.19e-4, 4.60e-4] |

The two Z runs differ by about 2 sigma (two-proportion test p = 0.049). I don't know why the
first one is low.

Per cycle, with X and Z failures combined (as in `examples/BivariateBicycleCodeAnalysis.ipynb`),
using the X run and both Z runs pooled (202 / 600,000):

    P_shot  = 1 - (1 - p_X)(1 - p_Z)
    p_cycle = 1 - (1 - P_shot)^(1/12)

This gives p_cycle = 6.1e-5, with a 95% CI of [5.4e-5, 6.8e-5] (delta method on P_shot).
With the first Z run alone it is 5.7e-5 [4.9e-5, 6.5e-5]; with the rerun alone, 6.5e-5.

## Regenerate

Needs a relay checkout with relay-bp installed (`pip install "./relay[stim]"`).

    RELAY_DIR=path/to/relay python run.py runs/relay_bp5_X.json
    RELAY_DIR=path/to/relay python run.py runs/relay_bp5_Z.json
    RELAY_DIR=path/to/relay python run.py runs/relay_bp5_Z_rerun.json
    python summarize.py

`summarize.py` writes `results.csv` and prints the per-cycle number, pooling every
`relay_bp5_Z*` run. Each 300k-shot run took 26 to 29 minutes. With 20 workers the machine ran out of memory, so use 10 or fewer on 16 GB.
