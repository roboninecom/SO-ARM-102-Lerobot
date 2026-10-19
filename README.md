# SO-ARM 102 for LeRobot

Set up, calibrate, and control an SO-ARM 102 follower with
[LeRobot](https://github.com/huggingface/lerobot). This package defines the arm's
motor layout, adds STS3235 support, and automatically reverses the follower gripper.

Use either an **SO-101 or SO-ARM 102 leader**. Both use STS3215 motors and LeRobot's
standard `so101_leader` configuration.

Supports both **Feetech SDK** and **Rustypot**, automatically selecting the
backend used by your LeRobot installation. Custom firmware support is planned
for a future release.

[Robot hardware and assembly](https://github.com/roboninecom/SO-ARM-102) ·
[SO-ARM 102 product page](https://robonine.com/shop/so-arm102-robotic-arm-kit/)

## Installation

Use Python 3.12. Follow the standard
[LeRobot installation guide](https://huggingface.co/docs/lerobot/en/installation)
for platform prerequisites, then install LeRobot and this plugin in the same
environment. For example, on macOS or Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install 'lerobot[feetech,core_scripts]==0.6.1'
python -m pip install 'lerobot_robot_so_arm102[feetech]==0.1.0a1'
```

If LeRobot 0.6.1 and its workflow dependencies are already installed, run only the
plugin installation command. Activate the same environment in each new terminal.
The exact plugin version selects the published alpha release.

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

Follow the prompts and move the joints through their ranges. Gripper direction
is handled automatically. Wrist roll assumes a
full-turn assembly. Keep the same arm IDs in later commands to reuse calibration.

## Teleoperate

By default, both arms use degrees (`use_degrees=true`): a 30° joint movement on
the leader requests a 30° movement on the follower. This does not scale a smaller
leader range to the follower's full range.

```bash
lerobot-teleoperate \
  --robot.type=so_arm102_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=so102_follower \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=so101_leader
```

To map the leader's full calibrated range to the follower's full calibrated
range, disable degrees on **both arms**:

```bash
lerobot-teleoperate \
  --robot.type=so_arm102_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=so102_follower \
  --robot.use_degrees=false \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=so101_leader \
  --teleop.use_degrees=false
```

This uses normalized joint positions from −100 to 100. A smaller leader range
can therefore cover a larger follower range. The gripper always uses 0–100,
independently of this setting. Existing calibration can be reused when switching
modes, provided it captures the intended travel. Keep the same position mode when
recording data and running a policy trained on that data.

Start with small movements and check that both grippers open together.
Press **Ctrl+C** to stop.

For recording and training, follow the [LeRobot guides](https://huggingface.co/docs/lerobot/en/index),
using `--robot.type=so_arm102_follower` and the same port and ID.

Maintainers: see [Publishing to PyPI](https://github.com/roboninecom/SO-ARM-102-Lerobot/blob/main/docs/publishing.md) for package versions,
release tags, TestPyPI checks, and Trusted Publisher setup.

## License

[Apache-2.0](https://github.com/roboninecom/SO-ARM-102-Lerobot/blob/main/LICENSE). See [NOTICE](https://github.com/roboninecom/SO-ARM-102-Lerobot/blob/main/NOTICE) for attribution.
