# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from lerobot.robots.config import RobotConfig
from lerobot.robots.so_follower.config_so_follower import SOFollowerConfig


@RobotConfig.register_subclass("so_arm102_follower")
@dataclass
class SOArm102FollowerConfig(RobotConfig, SOFollowerConfig):
    """SO follower settings with automatic motor backend selection."""

    controller: str = "auto"
