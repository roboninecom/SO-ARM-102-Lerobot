# SO-ARM 102 for LeRobot

Control an SO-ARM 102 follower with [LeRobot](https://github.com/huggingface/lerobot):
set up its motors, calibrate the arm, and teleoperate it with an SO-101 or SO-ARM 102 leader.
The package supports the arm's mixed STS3235, STS3250, and STS3215 motors and
handles the follower's reversed gripper direction automatically.

**Early alpha:** automated tests pass; full hardware validation is still pending.
This version supports standard Feetech firmware. Custom extended firmware support
is planned.

## Requirements

- Python 3.12, Git, and [uv](https://docs.astral.sh/uv/getting-started/installation/).
- An SO-ARM 102 follower with its USB controller and appropriate motor power supply.
- An SO-101 or SO-ARM 102 leader if you want to teleoperate the arm.
- The following motor layout, with matching firmware versions across the follower:

| ID  | Joint         | Motor   |
| --- | ------------- | ------- |
| 1   | Shoulder pan  | STS3235 |
| 2   | Shoulder lift | STS3250 |
| 3   | Elbow flex    | STS3250 |
| 4   | Wrist flex    | STS3235 |
| 5   | Wrist roll    | STS3215 |
| 6   | Gripper       | STS3215 |

Both supported leader arms use STS3215 motors on all joints and use LeRobot's
existing `so101_leader` configuration. No leader-specific changes are required;
use `--teleop.type=so101_leader` for either model throughout this guide.

The commands below are for macOS and Linux.

## 1. Install

```bash
git clone https://github.com/roboninecom/so-arm102-package.git
cd so-arm102-package

uv venv --python 3.12
source .venv/bin/activate

uv pip install \
  'lerobot[feetech] @ git+https://github.com/huggingface/lerobot.git@ae2b57f12223c8c5184fcd814eb63cd9ce7de203' \
  '.[feetech]'
```

This installs the package and the tested LeRobot revision together. A separate
LeRobot clone is not required. The package is not yet published on PyPI.

In each new terminal, return to this directory and run `source .venv/bin/activate`
before using the commands below.

## 2. Find the USB ports

Connect the follower's controller and run:

```bash
lerobot-find-port
```

Follow the unplug/reconnect prompts. Repeat for the leader if you have one.
Set these variables to the ports reported for your devices:

```bash
export FOLLOWER_PORT=/dev/ttyACM0
export LEADER_PORT=/dev/ttyACM1
```

On macOS, ports usually look like `/dev/cu.usbmodem…`. Use your actual port names;
the values above are examples. `LEADER_PORT` is only needed for leader setup and
teleoperation.

## 3. Set up motor IDs

**Skip this step if the follower already has the IDs shown in the table above.**
Motor setup changes IDs and baud rates. Connect only the motor requested by each
prompt, not the complete motor chain.

```bash
lerobot-setup-motors \
  --robot.type=so_arm102_follower \
  --robot.controller=feetech \
  --robot.port="$FOLLOWER_PORT"
```

After setup, reconnect the complete follower motor chain.

For a new SO-101 or SO-ARM 102 leader that has not been set up yet:

```bash
lerobot-setup-motors \
  --teleop.type=so101_leader \
  --teleop.port="$LEADER_PORT"
```

## 4. Calibrate

Place the follower where you can move its joints freely, then run:

```bash
lerobot-calibrate \
  --robot.type=so_arm102_follower \
  --robot.controller=feetech \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id=so102_follower
```

Follow the prompts to position the arm and move the joints through their ranges.
The follower stays torque-free during calibration. Wrist roll uses the SO arm's
full-turn range rather than measured stops; this assumes a full-turn wrist-roll
assembly. Gripper direction is handled automatically.

Calibrate the SO-101 or SO-ARM 102 leader separately using the same command:

```bash
lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port="$LEADER_PORT" \
  --teleop.id=so101_leader
```

Keep these IDs the same in later commands so LeRobot finds the saved calibrations.
Use different IDs for additional arms. If a calibration exists, press Enter to
reuse it or enter `c` to measure it again.

## 5. Teleoperate

```bash
lerobot-teleoperate \
  --robot.type=so_arm102_follower \
  --robot.controller=feetech \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id=so102_follower \
  --teleop.type=so101_leader \
  --teleop.port="$LEADER_PORT" \
  --teleop.id=so101_leader
```

Start with small leader movements and confirm that opening the leader gripper
opens the follower gripper. Press **Ctrl+C** to stop.

For recording demonstrations and training, follow the
[LeRobot documentation](https://huggingface.co/docs/lerobot/main/en/index).
Use `--robot.type=so_arm102_follower` and the same follower port, controller, and ID
in place of the standard SO-101 follower options.

## Optional: experimental Rustypot installation

Use this only if you want to try the Rustypot backend. It requires a different
LeRobot revision and a separate environment. From this repository directory:

```bash
uv venv --python 3.12 .venv-rustypot
source .venv-rustypot/bin/activate

uv pip install \
  'lerobot[feetech] @ git+https://github.com/huggingface/lerobot.git@8d3511625da34da5acceb8f67333578fa2fddab8' \
  'rustypot==1.11.0' \
  '.[rustypot]'
```

Then follow the same setup, calibration, and teleoperation steps, replacing every
`--robot.controller=feetech` with `--robot.controller=rustypot`. Installing Rustypot
alone in the default environment is not sufficient. To return to the default
installation, run `source .venv/bin/activate`.

## Troubleshooting

- **Robot type not found:** activate the environment where you installed this
  package. Check with `uv pip show lerobot_robot_so_arm102`.
- **Port not found or busy:** run `lerobot-find-port` again and close other programs
  using the controller, including another LeRobot session.
- **Incorrect motor model or missing motor:** check the wiring, motor IDs, and
  models against the table above. Motor identification is checked during connection.
- **Different firmware versions:** use matching firmware across the follower motors.
- **Using an older prototype:** recalibrate with this package before teleoperation;
  old prototype calibrations are not imported automatically.

## License

[Apache-2.0](LICENSE). See [NOTICE](NOTICE) for LeRobot attribution.
