# SO-ARM 102 LeRobot integration

An independently installable LeRobot robot plugin, developed here before moving
to its own repository. LeRobot core does not need modification.

The initial implementation uses the legacy Feetech backend with local STS3235
support. Rustypot compatibility is experimental. The future extended firmware
protocol is not implemented; it will use the same joint-level controller interface.

| ID  | Joint         | Model   |
| --- | ------------- | ------- |
| 1   | shoulder_pan  | STS3235 |
| 2   | shoulder_lift | STS3250 |
| 3   | elbow_flex    | STS3250 |
| 4   | wrist_flex    | STS3235 |
| 5   | wrist_roll    | STS3215 |
| 6   | gripper       | STS3215 |

Motor identification stays strict, including STS3235 model number 2057. Firmware
versions must match across the bus. Follower gripper calibration uses
`drive_mode=1`; the leader is unchanged. Inversion is applied once to observations
and commands by the controller, without changing the hardware Phase register.

## Local development

Requires Python 3.12. From the LeRobot repository root, use the existing environment:

```bash
uv pip install --python .venv/bin/python -e './packages/lerobot_robot_so_arm102[feetech,dev]'
uv run --no-sync pytest packages/lerobot_robot_so_arm102/tests
uv run --no-sync ruff check packages/lerobot_robot_so_arm102
uv run --no-sync ruff format --check packages/lerobot_robot_so_arm102
```

The package and import module both use `lerobot_robot_so_arm102`, as required by
LeRobot's plugin discovery. The config and robot are exported from `__init__.py`.
Do not install the old sibling prototype alongside this package in one environment:
they use the same distribution name and robot registration.

## Setup and calibration

Replace the port below with your controller's port. Motor setup prompts you to
connect only one motor at a time.

```bash
uv run --no-sync lerobot-setup-motors \
  --robot.type=so_arm102_follower --robot.controller=feetech \
  --robot.port=/dev/ttyACM0

uv run --no-sync lerobot-calibrate \
  --robot.type=so_arm102_follower --robot.controller=feetech \
  --robot.port=/dev/ttyACM0 --robot.id=so102_follower
```

`connect(calibrate=False)` leaves torque disabled for the calibration CLI. Normal
connection calibrates if needed, configures the motors, sets targets to the current
pose, and enables torque. Calibration uses the SO follower convention that
`wrist_roll` has a full 0..4095 range. Confirm that assumption for your assembly.
Hardware calibration and motion must be validated before release.

Calibration files are stored under a `feetech-sts-v1` subdirectory, including when
`calibration_dir` is supplied. Legacy Feetech and Rustypot share this format.
The old prototype's calibration files are not automatically imported. A future
controller with different calibration semantics must use a new schema directory.

## Controller boundary

`MotorController` exposes joint positions, configuration, torque, setup and
calibration. Register names and packet layouts stay in the backend. The robot
constructor accepts `controller=` for tests and future implementations. Body
positions use degrees or -100..100 according to `use_degrees`; the gripper uses
0..100. Selection is explicit and unsupported controllers fail without fallback.

Add extended firmware support when its wire specification and calibration
semantics are defined. No extended commands or automatic detection are assumed.

## Experimental Rustypot support

The tested combination is LeRobot PR #4672 at
`8d3511625da34da5acceb8f67333578fa2fddab8` with Rustypot 1.11.0. The adapter uses
the PR's private model lookup method; compatibility with later revisions must be
retested. Installing Rustypot alone does not convert a legacy LeRobot checkout.
Use a separate environment so the experimental install does not replace the
legacy development environment:

```bash
uv venv --python 3.12 .venv-rustypot
uv pip install --python .venv-rustypot/bin/python \
  'lerobot[feetech] @ git+https://github.com/huggingface/lerobot.git@8d3511625da34da5acceb8f67333578fa2fddab8' \
  'rustypot==1.11.0' -e './packages/lerobot_robot_so_arm102[rustypot,dev]'
uv run --no-project --python .venv-rustypot/bin/python \
  pytest -c packages/lerobot_robot_so_arm102/pyproject.toml packages/lerobot_robot_so_arm102/tests
```

Use that environment's `lerobot-calibrate` or `lerobot-teleoperate` executable
with `--robot.controller=rustypot`. The same robot type and joint mapping apply.
The adapter supplies model number 2057 with the shared STS definition only when
Rustypot does not already know STS3235. It does not alter Rustypot's global registry.

The tests select the installed LeRobot API and skip the other backend's tests.
They exercise actual SDK framing for Feetech and actual Rustypot definitions with
an injected transport for Rustypot; no real hardware is contacted. Both environments
must pass before claiming compatibility. Extended firmware will need its own
transport tests and hardware verification once specified.

## Publishing later

This directory is the package root; it can be copied to a standalone repository.
Its build metadata uses normal dependency constraints, not local paths or Git URLs.
The current compatibility baseline is LeRobot main at `ae2b57f1` (version 0.6.2).
Before release, test a published LeRobot version and tighten constraints accordingly;
the version range alone is not a claim that every commit has been tested.

From this directory:

```bash
uv build
uv run --with twine twine check dist/*
```

Before uploading, select an available PyPI name (keeping the `lerobot_robot_`
prefix), add the real repository URLs, validate installed-wheel discovery in a
clean environment, and test hardware setup, calibration and teleoperation. Publish
an alpha to TestPyPI first, then PyPI after verification. Uploading is a separate
release action; these build commands do not publish anything.

After the integration is public, submit a documentation-only PR adding the repository
to LeRobot's third-party robots page. Disclose significant AI assistance in any
upstream contribution, following LeRobot's contribution policy.

References:

- [LeRobot hardware integration](https://huggingface.co/docs/lerobot/main/en/integrate_hardware)
- [Third-party robots](https://huggingface.co/docs/lerobot/main/en/third_party_robots)
- [Python packaging guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Rustypot migration proposal](https://github.com/huggingface/lerobot/pull/4672)

Apache-2.0; see LICENSE and NOTICE for LeRobot attribution.
