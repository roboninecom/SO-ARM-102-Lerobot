# Experimental Rustypot backend

Rustypot requires the LeRobot API from [PR #4672](https://github.com/huggingface/lerobot/pull/4672).
Use the tested revision below in a separate environment. Installing Rustypot alone
with released LeRobot is not sufficient.

From this repository directory:

```bash
python3.12 -m venv .venv-rustypot
source .venv-rustypot/bin/activate
python -m pip install \
  'lerobot[feetech,core_scripts] @ git+https://github.com/huggingface/lerobot.git@8d3511625da34da5acceb8f67333578fa2fddab8' \
  '.[rustypot]'
```

Follow the [setup and usage guide](../README.md), adding
`--robot.controller=rustypot` to each follower command. Leader commands stay the same.

The legacy and Rustypot backends share calibration files. Automated tests cover
both backends; full hardware validation is pending.
