# SPDX-License-Identifier: Apache-2.0
import json
from dataclasses import asdict
from unittest.mock import Mock

import numpy as np
import pytest
from lerobot.cameras import Camera
from lerobot.motors.motors_bus import SerialMotorsBus
from lerobot.robots.config import RobotConfig
from lerobot.robots.so_follower import SOFollowerRobotConfig
from lerobot.utils.import_utils import make_device_from_device_class, register_third_party_plugins

from lerobot_robot_so_arm102 import SOArm102Follower, SOArm102FollowerConfig
from lerobot_robot_so_arm102.bus import make_bus


@pytest.fixture
def robot(tmp_path, fake_bus, input_responses):
    robot = SOArm102Follower(
        SOArm102FollowerConfig(port="unused", id="test", calibration_dir=tmp_path), bus=fake_bus
    )
    yield robot
    robot.disconnect()


@pytest.mark.parametrize("explicit_backend", [False, True])
@pytest.mark.parametrize("use_degrees", [False, True])
def test_discovery(tmp_path, explicit_backend, use_degrees):
    register_third_party_plugins()
    config_class = RobotConfig.get_choice_class("so_arm102_follower")
    assert config_class is SOArm102FollowerConfig
    backend = "rustypot" if hasattr(SerialMotorsBus, "_find_model") else "feetech"
    config = config_class(
        port="unused",
        calibration_dir=tmp_path,
        use_degrees=use_degrees,
        controller=backend if explicit_backend else "auto",
    )
    robot = make_device_from_device_class(config)
    assert isinstance(robot, SOArm102Follower)
    assert not robot.is_connected
    assert type(robot.bus).__name__ == (
        "SOArm102RustypotBus" if backend == "rustypot" else "SOArm102FeetechBus"
    )
    assert [(motor.id, motor.model) for motor in robot.bus.motors.values()] == [
        (1, "sts3235"),
        (2, "sts3250"),
        (3, "sts3250"),
        (4, "sts3235"),
        (5, "sts3215"),
        (6, "sts3215"),
    ]


def test_config_preserves_so_follower_defaults():
    config = asdict(SOArm102FollowerConfig(port="unused"))
    assert config.pop("controller") == "auto"
    assert config == asdict(SOFollowerRobotConfig(port="unused"))


def test_calibration_connection_uses_upstream_configuration(robot, fake_bus):
    robot.connect(calibrate=False)
    assert fake_bus.events == ["connect", "disable", "configure", "enable"]
    assert not robot.calibration
    assert set(robot.get_observation()) == set(robot.action_features)


def test_connect_failure_closes_bus(robot, fake_bus, calibration):
    fake_bus.calibration = calibration
    fake_bus.fail_configure = True
    with pytest.raises(RuntimeError, match="configuration failed"):
        robot.connect()
    assert not fake_bus.is_connected


@pytest.mark.parametrize("use_rgb, use_depth", [(True, False), (True, True), (False, True)])
def test_first_connection_with_camera_can_calibrate(robot, use_rgb, use_depth):
    camera = Mock(spec=Camera)
    camera.height, camera.width = 2, 3
    camera.is_connected = False
    camera.use_rgb, camera.use_depth = use_rgb, use_depth
    camera.connect.side_effect = lambda: setattr(camera, "is_connected", True)
    camera.disconnect.side_effect = lambda: setattr(camera, "is_connected", False)
    camera.read_latest.return_value = np.zeros((2, 3, 3), dtype=np.uint8)
    # Older camera interfaces provide this on concrete depth camera implementations.
    camera.read_latest_depth = Mock(return_value=np.zeros((2, 3, 1), dtype=np.uint16))
    robot.cameras["test"] = camera
    robot.connect()
    assert robot.is_calibrated
    observation = robot.get_observation()
    assert set(observation) == set(robot.observation_features)
    assert ("test" in observation) == use_rgb
    assert ("test_depth" in observation) == use_depth
    for name in ("test", "test_depth"):
        if name in observation:
            assert observation[name].shape == robot.observation_features[name]
    robot.disconnect()
    assert not camera.is_connected


def test_calibration_persists_inversion_and_reloads_existing_path(robot, fake_bus, tmp_path):
    robot.connect(calibrate=False)
    robot.calibrate()
    assert robot.calibration_fpath == tmp_path / "feetech-sts-v1" / "test.json"
    saved = json.loads(robot.calibration_fpath.read_text())
    assert {joint: cal["drive_mode"] for joint, cal in saved.items()} == {
        joint: int(joint == "gripper") for joint in fake_bus.motors
    }
    reloaded = SOArm102Follower(robot.config)
    assert reloaded.calibration == robot.calibration == fake_bus.calibration
    assert reloaded.bus.calibration == robot.calibration
    robot.calibrate()  # Reusing the file preserves inversion, too.
    assert robot.calibration["gripper"].drive_mode == 1


def test_existing_non_inverted_calibration_is_corrected(robot, fake_bus, calibration):
    calibration["gripper"].drive_mode = 0
    robot.calibration = calibration
    robot.calibrate()
    assert fake_bus.calibration["gripper"].drive_mode == 1
    assert json.loads(robot.calibration_fpath.read_text())["gripper"]["drive_mode"] == 1


def test_action_clipping(robot, fake_bus):
    robot.config.max_relative_target = 5.0
    robot.connect(calibrate=False)
    sent = robot.send_action({"shoulder_pan.pos": 20})
    assert sent == {"shoulder_pan.pos": 5}
    assert fake_bus.positions["shoulder_pan"] == 5


def test_setup_releases_bus(robot, fake_bus):
    fake_bus.connect()
    robot.setup_motors()
    assert fake_bus.events[1:-1] == list(reversed(fake_bus.motors))
    assert not fake_bus.is_connected


def test_unknown_controller_fails_without_fallback():
    with pytest.raises(ValueError, match="Unknown controller"):
        make_bus(SOArm102FollowerConfig(port="unused", controller="extended"))


def test_backend_mismatch_has_actionable_error():
    backend = "feetech" if hasattr(SerialMotorsBus, "_find_model") else "rustypot"
    with pytest.raises(RuntimeError, match="[Rr]ustypot"):
        make_bus(SOArm102FollowerConfig(port="unused", controller=backend))
