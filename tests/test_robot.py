# SPDX-License-Identifier: Apache-2.0
import pytest
from lerobot.robots.config import RobotConfig
from lerobot.utils.import_utils import make_device_from_device_class, register_third_party_plugins

from lerobot_robot_so_arm102 import SOArm102Follower, SOArm102FollowerConfig
from lerobot_robot_so_arm102.controller import make_controller


@pytest.fixture
def robot(tmp_path, controller):
    robot = SOArm102Follower(
        SOArm102FollowerConfig(port="unused", id="test", calibration_dir=tmp_path), controller=controller
    )
    yield robot
    robot.disconnect()


def test_discovery(tmp_path):
    register_third_party_plugins()
    config_class = RobotConfig.get_choice_class("so_arm102_follower")
    assert config_class is SOArm102FollowerConfig
    config = config_class(port="unused", calibration_dir=tmp_path)
    # The installed plugin is discovered and constructed through LeRobot, without hardware IO.
    robot = make_device_from_device_class(config)
    assert isinstance(robot, SOArm102Follower)
    assert not robot.is_connected


def test_calibration_connection_never_enables_torque(robot, controller):
    robot.connect(calibrate=False)
    assert controller.events == ["connect", "disable"]
    assert set(robot.get_observation()) == set(robot.action_features)


def test_normal_connection_holds_current_pose_before_torque(robot, controller, calibration):
    robot.calibration = calibration
    robot.connect()
    assert controller.events == ["connect", "disable", "configure", "write", "enable"]


def test_connect_failure_closes_controller(robot, controller, calibration):
    robot.calibration = calibration
    controller.fail_configure = True
    with pytest.raises(RuntimeError, match="configuration failed"):
        robot.connect()
    assert not controller.is_connected
    assert "enable" not in controller.events


def test_calibration_persists_follower_direction_and_schema(robot, controller, tmp_path):
    robot.connect(calibrate=False)
    robot.calibrate()
    assert robot.calibration["gripper"].drive_mode == 1
    assert robot.calibration["shoulder_pan"].drive_mode == 0
    assert robot.calibration_fpath == tmp_path / "feetech-sts-v1" / "test.json"
    assert robot.calibration_fpath.is_file()
    assert controller.calibration == robot.calibration
    assert "enable" not in controller.events


def test_different_protocol_does_not_load_legacy_calibration(robot, controller, tmp_path):
    robot.connect(calibrate=False)
    robot.calibrate()
    controller.calibration_schema = "extended-v1"
    extended = SOArm102Follower(robot.config, controller=controller)
    assert extended.calibration == {}
    assert extended.calibration_fpath == tmp_path / "extended-v1" / "test.json"


def test_action_clipping(robot, controller):
    robot.config.max_relative_target = 5.0
    robot.connect(calibrate=False)
    sent = robot.send_action({"shoulder_pan.pos": 20})
    assert sent == {"shoulder_pan.pos": 5}
    assert controller.positions["shoulder_pan"] == 5


def test_unknown_controller_fails_without_fallback():
    with pytest.raises(ValueError, match="Unknown controller"):
        make_controller(SOArm102FollowerConfig(port="unused", controller="extended"))
