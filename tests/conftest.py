# SPDX-License-Identifier: Apache-2.0
from dataclasses import replace

import pytest
from lerobot.motors import MotorCalibration
from lerobot.motors.motors_bus import SerialMotorsBus

from lerobot_robot_so_arm102.bus import MOTOR_MODELS, make_motors


@pytest.fixture
def calibration():
    return {
        joint: MotorCalibration(
            id=id_, drive_mode=int(joint == "gripper"), homing_offset=0, range_min=100, range_max=4000
        )
        for id_, joint in enumerate(MOTOR_MODELS, 1)
    }


class FakeBus:
    torque_disabled = SerialMotorsBus.torque_disabled

    def __init__(self, calibration):
        self.motors = make_motors(True)
        self.calibration = {}
        self.measured_calibration = calibration
        self.is_connected = False
        self.positions = dict.fromkeys(MOTOR_MODELS, 0.0)
        self.events = []
        self.fail_configure = False

    @property
    def is_calibrated(self):
        return bool(self.calibration)

    def connect(self):
        self.is_connected = True
        self.events.append("connect")

    def disconnect(self, disable_torque=True):
        self.is_connected = False
        self.events.append("disconnect")

    def disable_torque(self, motors=None):
        self.events.append("disable")

    def enable_torque(self, motors=None):
        self.events.append("enable")

    def configure_motors(self):
        if self.fail_configure:
            raise RuntimeError("configuration failed")
        self.events.append("configure")

    def write(self, name, motor, value):
        pass

    def set_operating_mode(self, mode, motors=None):
        pass

    def write_calibration(self, calibration):
        self.calibration = calibration

    def set_half_turn_homings(self):
        return dict.fromkeys(self.motors, 0)

    def record_ranges_of_motion(self, motors):
        return dict.fromkeys(motors, 100), dict.fromkeys(motors, 4000)

    def record_calibration(self, mode, full_turn_motors):
        return {joint: replace(cal, drive_mode=0) for joint, cal in self.measured_calibration.items()}

    def sync_read(self, name, num_retry=0):
        return self.positions.copy()

    def sync_write(self, name, positions):
        self.positions.update(positions)

    def setup_motor(self, motor):
        self.events.append(motor)

    def setup_motors(self):
        for motor in reversed(self.motors):
            self.setup_motor(motor)


@pytest.fixture
def fake_bus(calibration):
    return FakeBus(calibration)


@pytest.fixture
def input_responses(monkeypatch):
    responses = []
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0) if responses else "")
    return responses
