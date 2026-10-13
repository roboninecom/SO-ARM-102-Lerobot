# SPDX-License-Identifier: Apache-2.0
# Camera and action handling adapted from LeRobot's SOFollower.
import logging
from dataclasses import replace
from functools import cached_property

from lerobot.cameras import DepthCamera, make_cameras_from_configs
from lerobot.lerobot_types import RobotAction, RobotObservation
from lerobot.robots import Robot
from lerobot.robots.utils import ensure_safe_goal_position
from lerobot.utils.constants import HF_LEROBOT_CALIBRATION, ROBOTS
from lerobot.utils.decorators import check_if_already_connected, check_if_not_connected

from .config_so_arm102 import SOArm102FollowerConfig
from .controller import MOTOR_MODELS, MotorController, make_controller

logger = logging.getLogger(__name__)


class SOArm102Follower(Robot):
    """SO-ARM 102 follower with an injectable joint controller and inverted gripper."""

    config_class = SOArm102FollowerConfig
    name = "so_arm102_follower"
    supports_position_hold = True

    def __init__(self, config: SOArm102FollowerConfig, *, controller: MotorController | None = None):
        self.controller = controller if controller is not None else make_controller(config)
        # Both legacy implementations share calibration semantics. A future protocol opts
        # into a new namespace rather than silently reusing incompatible offsets/ranges.
        directory = config.calibration_dir or HF_LEROBOT_CALIBRATION / ROBOTS / self.name
        super().__init__(replace(config, calibration_dir=directory / self.controller.calibration_schema))
        self.config = config
        self.cameras = make_cameras_from_configs(config.cameras)

    @cached_property
    def action_features(self) -> dict[str, type]:
        return {f"{joint}.pos": float for joint in MOTOR_MODELS}

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        features: dict[str, type | tuple] = dict(self.action_features)
        for name, camera in self.cameras.items():
            if getattr(camera, "use_rgb", True):
                features[name] = (camera.height, camera.width, 3)
            if isinstance(camera, DepthCamera) and camera.use_depth:
                features[f"{name}_depth"] = (camera.height, camera.width, 1)
        return features

    @property
    def is_connected(self) -> bool:
        return self.controller.is_connected and all(camera.is_connected for camera in self.cameras.values())

    @property
    def is_calibrated(self) -> bool:
        if set(self.calibration) != set(MOTOR_MODELS):
            return False
        if any(
            self.calibration[joint].id != id_ or self.calibration[joint].drive_mode != int(joint == "gripper")
            for id_, joint in enumerate(MOTOR_MODELS, 1)
        ):
            return False
        return self.controller.is_calibrated(self.calibration)

    @check_if_already_connected
    def connect(self, calibrate: bool = True) -> None:
        """Connect with torque off; enable position control only for normal operation."""
        try:
            self.controller.connect()
            self.controller.disable_torque()
            if calibrate and not self.is_calibrated:
                self.calibrate()
            for camera in self.cameras.values():
                camera.connect()
            if calibrate:
                self.configure()
                self.controller.write_positions(self.controller.read_positions())
                self.controller.enable_torque()
        except BaseException:
            try:
                self.disconnect()
            except Exception:
                logger.exception("Cleanup failed after connection error")
            raise

    @check_if_not_connected
    def calibrate(self) -> None:
        """Reuse compatible calibration or measure fresh ranges with torque disabled."""
        self.controller.disable_torque()
        reuse = (
            self.calibration
            and input("Press ENTER to reuse calibration, or type 'c' to recalibrate: ").strip().lower() != "c"
        )
        calibration = self.calibration if reuse else self.controller.calibrate()
        if set(calibration) != set(MOTOR_MODELS):
            raise ValueError("Calibration must contain all six SO-ARM 102 joints.")
        calibration = {
            joint: replace(cal, drive_mode=int(joint == "gripper")) for joint, cal in calibration.items()
        }
        self.controller.apply_calibration(calibration)
        self.calibration = calibration
        self._save_calibration()

    def configure(self) -> None:
        """Apply controller settings without enabling torque."""
        self.controller.configure()

    def setup_motors(self) -> None:
        """Assign motor IDs one at a time using the selected controller."""
        try:
            self.controller.setup_motors()
        finally:
            self.controller.disconnect()

    @check_if_not_connected
    def get_observation(self) -> RobotObservation:
        observation = {f"{joint}.pos": value for joint, value in self.controller.read_positions().items()}
        for name, camera in self.cameras.items():
            if getattr(camera, "use_rgb", True):
                observation[name] = camera.read_latest()
            if isinstance(camera, DepthCamera) and camera.use_depth:
                observation[f"{name}_depth"] = camera.read_latest_depth()
        return observation

    @check_if_not_connected
    def send_action(self, action: RobotAction) -> RobotAction:
        positions = {key.removesuffix(".pos"): value for key, value in action.items() if key.endswith(".pos")}
        if self.config.max_relative_target is not None:
            present = self.controller.read_positions()
            positions = ensure_safe_goal_position(
                {joint: (target, present[joint]) for joint, target in positions.items()},
                self.config.max_relative_target,
            )
        self.controller.write_positions(positions)
        return {f"{joint}.pos": value for joint, value in positions.items()}

    def disconnect(self) -> None:
        """Close the controller and cameras, including after a partial connection."""
        try:
            self.controller.disconnect(self.config.disable_torque_on_disconnect)
        finally:
            for camera in self.cameras.values():
                if camera.is_connected:
                    camera.disconnect()
