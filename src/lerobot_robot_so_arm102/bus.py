# SPDX-License-Identifier: Apache-2.0
from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.motors.motors_bus import SerialMotorsBus
from lerobot.utils.import_utils import require_package

from .config_so_arm102 import SOArm102FollowerConfig

MOTOR_MODELS = {
    "shoulder_pan": "sts3235",
    "shoulder_lift": "sts3250",
    "elbow_flex": "sts3250",
    "wrist_flex": "sts3235",
    "wrist_roll": "sts3215",
    "gripper": "sts3215",
}


def make_motors(use_degrees: bool) -> dict[str, Motor]:
    """Build the fixed SO-ARM 102 wiring and normalization map."""
    body_mode = MotorNormMode.DEGREES if use_degrees else MotorNormMode.RANGE_M100_100
    return {
        joint: Motor(id_, model, MotorNormMode.RANGE_0_100 if joint == "gripper" else body_mode)
        for id_, (joint, model) in enumerate(MOTOR_MODELS.items(), 1)
    }


def make_bus(
    config: SOArm102FollowerConfig, calibration: dict[str, MotorCalibration] | None = None
) -> SerialMotorsBus:
    """Construct the installed LeRobot backend with the SO-ARM 102 motor layout."""
    backend = config.controller
    if backend == "auto":
        backend = "rustypot" if hasattr(SerialMotorsBus, "_find_model") else "feetech"
    bus_class: type[SerialMotorsBus]
    if backend == "feetech":
        if hasattr(SerialMotorsBus, "_find_model"):
            raise RuntimeError("This LeRobot uses Rustypot; select controller='rustypot'.")
        from .backends.feetech import SOArm102FeetechBus

        bus_class = SOArm102FeetechBus
    elif backend == "rustypot":
        if not hasattr(SerialMotorsBus, "_find_model"):
            raise RuntimeError(
                "controller='rustypot' requires the Rustypot-backed LeRobot API. "
                "Install a LeRobot version with Rustypot support."
            )
        require_package("rustypot", extra="rustypot")
        from .backends.rustypot import SOArm102RustypotBus

        bus_class = SOArm102RustypotBus
    else:
        raise ValueError(f"Unknown controller {config.controller!r}; choose 'auto', 'feetech' or 'rustypot'.")
    return bus_class(config.port, make_motors(config.use_degrees), calibration=calibration)
