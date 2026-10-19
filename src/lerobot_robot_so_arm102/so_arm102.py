# SPDX-License-Identifier: Apache-2.0
from contextlib import suppress
from dataclasses import replace

from lerobot.motors.motors_bus import SerialMotorsBus
from lerobot.robots.so_follower import SOFollower
from lerobot.utils.constants import HF_LEROBOT_CALIBRATION, ROBOTS
from lerobot.utils.decorators import check_if_already_connected

from .bus import make_bus
from .config_so_arm102 import SOArm102FollowerConfig


class SOArm102Follower(SOFollower):
    """SO follower with the SO-ARM 102 motor layout and an inverted gripper."""

    config_class = SOArm102FollowerConfig
    name = "so_arm102_follower"
    supports_position_hold = True

    def __init__(self, config: SOArm102FollowerConfig, *, bus: SerialMotorsBus | None = None):
        directory = config.calibration_dir or HF_LEROBOT_CALIBRATION / ROBOTS / self.name
        # Preserve calibration files created by earlier plugin releases.
        super().__init__(replace(config, calibration_dir=directory / "feetech-sts-v1"))
        self.config = config
        self.bus = bus if bus is not None else make_bus(config, self.calibration)
        self.bus.calibration = self.calibration

    @check_if_already_connected
    def connect(self, calibrate: bool = True) -> None:
        try:
            super().connect(calibrate=calibrate)
        except BaseException:
            with suppress(Exception):
                self.disconnect()
            raise

    def calibrate(self) -> None:
        super().calibrate()
        self.calibration["gripper"] = replace(self.calibration["gripper"], drive_mode=1)
        self.bus.write_calibration(self.calibration)
        self._save_calibration()

    def setup_motors(self) -> None:
        try:
            super().setup_motors()
        finally:
            self.disconnect()

    def disconnect(self) -> None:
        try:
            if self.bus.is_connected:
                self.bus.disconnect(self.config.disable_torque_on_disconnect)
        finally:
            for camera in self.cameras.values():
                if camera.is_connected:
                    camera.disconnect()
