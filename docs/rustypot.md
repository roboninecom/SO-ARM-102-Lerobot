# LeRobot from GitHub (Rustypot)

Current LeRobot main uses Rustypot for Feetech motor control. Install it in a
separate environment from the PyPI release:

```bash
git clone https://github.com/huggingface/lerobot.git
cd lerobot
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[serial-motors,core_scripts]'

git clone https://github.com/roboninecom/so-arm102-package.git
python -m pip install -e './so-arm102-package[rustypot]'
```

Follow the [setup and usage guide](../README.md). The plugin selects Rustypot
automatically; no extra controller flag is needed. The same commands also work
with the PyPI installation, where the plugin selects the legacy Feetech SDK.

To select a backend explicitly, use `--robot.controller=rustypot` or
`--robot.controller=feetech`. An incompatible choice reports an error. Leader
commands stay the same for SO-101 and SO-ARM 102 leaders.

Both backends use standard Feetech firmware and share calibration files. Automated
tests cover both; full hardware validation is pending. The old experimental
Rustypot PR revision is no longer supported; use current LeRobot main with
Rustypot 1.13.1 or newer (below 2.0).
