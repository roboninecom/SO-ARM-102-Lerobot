# SPDX-License-Identifier: Apache-2.0
from importlib import import_module
from typing import Protocol

from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.motors.motors_bus import SerialMotorsBus

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


class MotorController(Protocol):
    """Joint-level boundary for legacy drivers and future custom firmware.

    Position values use the configured body units and 0..100 gripper range.
    Controllers apply calibration direction exactly once in both directions.
    A different calibration representation must use a different schema name.
    """

    calibration_schema: str

    @property
    def is_connected(self) -> bool: ...
    def connect(self) -> None: ...
    def disconnect(self, disable_torque: bool = True) -> None: ...
    def configure(self) -> None: ...
    def enable_torque(self) -> None: ...
    def disable_torque(self) -> None: ...
    def is_calibrated(self, calibration: dict[str, MotorCalibration]) -> bool: ...
    def apply_calibration(self, calibration: dict[str, MotorCalibration]) -> None: ...
    def calibrate(self) -> dict[str, MotorCalibration]: ...
    def setup_motors(self) -> None: ...
    def read_positions(self) -> dict[str, float]: ...
    def write_positions(self, positions: dict[str, float]) -> None: ...


def make_controller(config: SOArm102FollowerConfig) -> MotorController:
    """Load only the selected driver; optional SDKs are not needed for discovery."""
    if config.controller not in ("feetech", "rustypot"):
        raise ValueError(f"Unknown controller {config.controller!r}; choose 'feetech' or 'rustypot'.")
    # The old module is only a deprecated alias after the Rustypot migration.
    if config.controller == "feetech":
        if hasattr(SerialMotorsBus, "_find_model"):
            raise RuntimeError("This LeRobot uses Rustypot; select controller='rustypot'.")
    module = import_module(f".backends.{config.controller}", __package__)
    return module.make_controller(config)
