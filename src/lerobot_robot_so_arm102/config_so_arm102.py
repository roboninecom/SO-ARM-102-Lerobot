# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from lerobot.robots.config import RobotConfig


@RobotConfig.register_subclass("so_arm102_follower")
@dataclass
class SOArm102FollowerConfig(RobotConfig):
    """SO-ARM 102 configuration; controller selection is explicit and never falls back."""

    port: str
    controller: str = "feetech"
    cameras: dict[str, CameraConfig] = field(default_factory=dict)
    use_degrees: bool = True
    disable_torque_on_disconnect: bool = True
    max_relative_target: float | dict[str, float] | None = None
    num_read_retries: int = 2
    position_p_coefficient: int = 16
    position_i_coefficient: int = 0
    position_d_coefficient: int = 32
