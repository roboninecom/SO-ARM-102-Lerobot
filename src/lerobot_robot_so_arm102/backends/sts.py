# SPDX-License-Identifier: Apache-2.0
# Settings and calibration procedure adapted from LeRobot's SOFollower.
from lerobot.motors import MotorCalibration
from lerobot.motors.motors_bus import SerialMotorsBus

from ..config_so_arm102 import SOArm102FollowerConfig


class STSController:
    """Joint-level operations shared by the two legacy STS bus implementations."""

    calibration_schema = "feetech-sts-v1"

    def __init__(self, bus: SerialMotorsBus, config: SOArm102FollowerConfig):
        self.bus = bus
        self.config = config

    @property
    def is_connected(self) -> bool:
        return self.bus.is_connected

    def connect(self) -> None:
        self.bus.connect()

    def disconnect(self, disable_torque: bool = True) -> None:
        if self.is_connected:
            self.bus.disconnect(disable_torque=disable_torque)

    def enable_torque(self) -> None:
        self.bus.enable_torque()

    def disable_torque(self) -> None:
        self.bus.disable_torque()

    def configure(self) -> None:
        """Keep torque off while applying the usual SO follower settings."""
        self.disable_torque()
        self.bus.configure_motors()
        for joint in self.bus.motors:
            self.bus.write("Operating_Mode", joint, 0)
            self.bus.write("P_Coefficient", joint, self.config.position_p_coefficient)
            self.bus.write("I_Coefficient", joint, self.config.position_i_coefficient)
            self.bus.write("D_Coefficient", joint, self.config.position_d_coefficient)
        self.bus.write("Max_Torque_Limit", "gripper", 500)
        self.bus.write("Protection_Current", "gripper", 250)
        self.bus.write("Overload_Torque", "gripper", 25)

    def is_calibrated(self, calibration: dict[str, MotorCalibration]) -> bool:
        self.bus.calibration = calibration
        return self.bus.is_calibrated

    def apply_calibration(self, calibration: dict[str, MotorCalibration]) -> None:
        self.bus.write_calibration(calibration)

    def calibrate(self) -> dict[str, MotorCalibration]:
        """Measure STS offsets and ranges; retain the SO full-turn wrist-roll convention."""
        self.disable_torque()
        for joint in self.bus.motors:
            self.bus.write("Operating_Mode", joint, 0)
        input("Move the arm to the middle of its range of motion, then press ENTER: ")
        offsets = self.bus.set_half_turn_homings()
        joints = [joint for joint in self.bus.motors if joint != "wrist_roll"]
        print("Move each joint except wrist_roll through its full range. Press ENTER to finish.")
        minimums, maximums = self.bus.record_ranges_of_motion(joints)
        minimums["wrist_roll"], maximums["wrist_roll"] = 0, 4095
        return {
            joint: MotorCalibration(
                id=motor.id,
                drive_mode=int(joint == "gripper"),
                homing_offset=int(offsets[joint]),
                range_min=int(minimums[joint]),
                range_max=int(maximums[joint]),
            )
            for joint, motor in self.bus.motors.items()
        }

    def setup_motors(self) -> None:
        for joint in reversed(self.bus.motors):
            input(f"Connect only the '{joint}' motor to the controller, then press ENTER: ")
            self.bus.setup_motor(joint)

    def read_positions(self) -> dict[str, float]:
        return self.bus.sync_read("Present_Position", num_retry=self.config.num_read_retries)

    def write_positions(self, positions: dict[str, float]) -> None:
        self.bus.sync_write("Goal_Position", positions)
