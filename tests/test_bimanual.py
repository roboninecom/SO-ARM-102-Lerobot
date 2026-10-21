# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy

import draccus
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.scripts.lerobot_calibrate import CalibrateConfig
from lerobot.utils.import_utils import make_device_from_device_class, register_third_party_plugins

from lerobot_robot_so_arm102 import BiSOArm102Follower, SOArm102Follower
from lerobot_robot_so_arm102.bus import MOTOR_MODELS


def make_config(tmp_path):
    register_third_party_plugins()
    return draccus.parse(
        CalibrateConfig,
        args=[
            "--robot.type=bi_so_arm102_follower",
            "--robot.id=pair",
            f"--robot.calibration_dir={tmp_path}",
            "--robot.left_arm_config.port=left-unused",
            "--robot.right_arm_config.port=right-unused",
            "--robot.left_arm_config.use_degrees=false",
            "--robot.right_arm_config.use_degrees=false",
            "--robot.left_arm_config.position_p_coefficient=20",
        ],
    ).robot


def test_bimanual_discovery_and_per_arm_settings(tmp_path):
    robot = make_device_from_device_class(make_config(tmp_path))
    assert isinstance(robot, BiSOArm102Follower)
    assert not robot.is_connected
    for side in ("left", "right"):
        arm = getattr(robot, f"{side}_arm")
        assert isinstance(arm, SOArm102Follower)
        assert arm.id == f"pair_{side}"
        assert arm.config.port == f"{side}-unused"
        assert not arm.config.use_degrees
        assert arm.calibration_fpath == tmp_path / "feetech-sts-v1" / f"pair_{side}.json"
        assert {joint: motor.model for joint, motor in arm.bus.motors.items()} == MOTOR_MODELS
    assert robot.left_arm.config.position_p_coefficient == 20
    assert len(robot.action_features) == 12
    assert robot.observation_features == robot.action_features


def test_bimanual_action_and_observation_routing(tmp_path, fake_bus):
    robot = make_device_from_device_class(make_config(tmp_path))
    robot.left_arm.bus = fake_bus
    robot.right_arm.bus = deepcopy(fake_bus)
    robot.connect(calibrate=False)
    try:
        action = {key: float(index) for index, key in enumerate(robot.action_features)}
        assert robot.send_action(action) == action
        assert robot.get_observation() == action
    finally:
        robot.disconnect()
    assert not robot.left_arm.is_connected
    assert not robot.right_arm.is_connected


def test_bimanual_camera_configuration_is_preserved(tmp_path):
    config = make_config(tmp_path)
    config.cameras = {"overhead": OpenCVCameraConfig(index_or_path=0, width=640, height=480, fps=30)}
    config.right_arm_config.cameras = {
        "wrist": OpenCVCameraConfig(index_or_path=1, width=640, height=480, fps=30)
    }
    robot = make_device_from_device_class(config)
    assert set(robot.cameras) == {"overhead", "wrist"}
    assert robot.cameras["overhead"] is robot.left_arm.cameras["overhead"]
    assert robot.cameras["wrist"] is robot.right_arm.cameras["wrist"]
    assert robot.observation_features["overhead"] == (480, 640, 3)
    assert robot.observation_features["right_wrist"] == (480, 640, 3)
