# Contributing

- A new fault is a new `FaultSubType` branch in the GPS or IMU publisher (see `patch/`), plus an example in `injections/`.
- Keep campaigns reproducible: record the seed label, the fault values and the PX4 commit with every result.
- Run `python3 -m py_compile` on changed scripts and, for harness changes, one gold flight before opening a pull request.
