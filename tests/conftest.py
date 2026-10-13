# SPDX-License-Identifier: Apache-2.0
import pytest
from lerobot.motors import MotorCalibration

from lerobot_robot_so_arm102.controller import MOTOR_MODELS


@pytest.fixture
def calibration():
    return {
        joint: MotorCalibration(
            id=id_, drive_mode=int(joint == "gripper"), homing_offset=0, range_min=100, range_max=4000
        )
        for id_, joint in enumerate(MOTOR_MODELS, 1)
    }


class FakeController:
    calibration_schema = "feetech-sts-v1"

    def __init__(self, calibration):
        self.is_connected = False
        self.calibration = calibration
        self.events = []
        self.positions = dict.fromkeys(MOTOR_MODELS, 0.0)
        self.fail_configure = False

    def connect(self):
        self.is_connected = True
        self.events.append("connect")

    def disconnect(self, disable_torque=True):
        self.is_connected = False
        self.events.append("disconnect")

    def configure(self):
        self.events.append("configure")
        if self.fail_configure:
            raise RuntimeError("configuration failed")

    def enable_torque(self):
        self.events.append("enable")

    def disable_torque(self):
        self.events.append("disable")

    def is_calibrated(self, calibration):
        return calibration == self.calibration

    def apply_calibration(self, calibration):
        self.calibration = calibration

    def calibrate(self):
        return self.calibration.copy()

    def setup_motors(self):
        self.events.append("setup")

    def read_positions(self):
        return self.positions.copy()

    def write_positions(self, positions):
        self.events.append("write")
        self.positions.update(positions)


@pytest.fixture
def controller(calibration):
    return FakeController(calibration)
