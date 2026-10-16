# SO-ARM 102 for LeRobot

Set up, calibrate, and control an SO-ARM 102 follower with
[LeRobot](https://github.com/huggingface/lerobot). This package supports its mixed
STS3235, STS3250, and STS3215 motors and automatically reverses the follower gripper.

Use either an **SO-101 or SO-ARM 102 leader**. Both use STS3215 motors and LeRobot's
standard `so101_leader` configuration.

Early alpha: automated tests are available; full hardware validation is pending.

## Installation

Use Python 3.12 or newer. Follow the standard
[LeRobot installation guide](https://huggingface.co/docs/lerobot/en/installation)
for your platform, then install LeRobot with Feetech and robot workflow support.
For example, on macOS or Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install 'lerobot[feetech,core_scripts]>=0.6.1,<0.7'
```

Install this plugin in the **same environment**:

```bash
git clone https://github.com/roboninecom/so-arm102-package.git
cd so-arm102-package
python -m pip install .
```

If you already have a compatible LeRobot environment with Feetech support, only
install the plugin. It is not yet published on PyPI. Activate the same environment
in each new terminal.

## Connect and set up

Connect the powered follower and leader controllers. Run `lerobot-find-port` for
each arm. In the commands below, replace `/dev/ttyACM0` with your follower port and
`/dev/ttyACM1` with your leader port. On macOS, ports usually start with
`/dev/cu.usbmodem`.

The follower expects this layout and matching firmware versions:

| ID  | Joint         | Motor   |
| --- | ------------- | ------- |
| 1   | Shoulder pan  | STS3235 |
| 2   | Shoulder lift | STS3250 |
| 3   | Elbow flex    | STS3250 |
| 4   | Wrist flex    | STS3235 |
| 5   | Wrist roll    | STS3215 |
| 6   | Gripper       | STS3215 |

**Skip motor setup for arms that are already configured.** Otherwise, run the
appropriate command and connect only the motor requested by each prompt:

```bash
lerobot-setup-motors --robot.type=so_arm102_follower --robot.port=/dev/ttyACM0
lerobot-setup-motors --teleop.type=so101_leader --teleop.port=/dev/ttyACM1
```

Reconnect the full motor chain after setup.

## Calibrate

```bash
lerobot-calibrate \
  --robot.type=so_arm102_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=so102_follower

lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=so101_leader
```

Follow the prompts and move the joints through their ranges. The follower stays
torque-free; gripper direction is handled automatically. Wrist roll assumes a
full-turn assembly. Keep the same arm IDs in later commands to reuse calibration.

## Teleoperate

```bash
lerobot-teleoperate \
  --robot.type=so_arm102_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=so102_follower \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=so101_leader
```

Start with small movements and check that both grippers open together.
Press **Ctrl+C** to stop.

For recording and training, follow the [LeRobot guides](https://huggingface.co/docs/lerobot/en/index),
using `--robot.type=so_arm102_follower` and the same port and ID.

Standard Feetech firmware is supported by default. For the experimental Rustypot
backend, see [Rustypot installation](docs/rustypot.md). Custom firmware support is planned.

## License

Maintainers: see [Publishing to PyPI](docs/publishing.md) for release automation
and one-time Trusted Publisher setup.

[Apache-2.0](LICENSE). See [NOTICE](NOTICE) for attribution.
