# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from lerobot.robots.bi_so_follower import BiSOFollowerConfig
from lerobot.robots.config import RobotConfig


@RobotConfig.register_subclass("bi_so_arm102_follower")
@dataclass
class BiSOArm102FollowerConfig(BiSOFollowerConfig):
    """Two SO-ARM 102 followers with standard LeRobot per-arm settings."""

    controller: str = "auto"
