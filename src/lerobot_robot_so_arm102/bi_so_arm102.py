# SPDX-License-Identifier: Apache-2.0
from lerobot.robots.bi_so_follower import BiSOFollower

from .config_bi_so_arm102 import BiSOArm102FollowerConfig
from .config_so_arm102 import SOArm102FollowerConfig
from .so_arm102 import SOArm102Follower


class BiSOArm102Follower(BiSOFollower):
    """Reuse LeRobot's bimanual routing with two SO-ARM 102 followers."""

    config_class = BiSOArm102FollowerConfig
    name = "bi_so_arm102_follower"
    supports_position_hold = True

    def __init__(self, config: BiSOArm102FollowerConfig):
        super().__init__(config)
        # Upstream prepares per-arm IDs, settings and cameras without opening ports.
        self.left_arm = SOArm102Follower(
            SOArm102FollowerConfig(**vars(self.left_arm.config), controller=config.controller)
        )
        self.right_arm = SOArm102Follower(
            SOArm102FollowerConfig(**vars(self.right_arm.config), controller=config.controller)
        )
        self.cameras = {**self.left_arm.cameras, **self.right_arm.cameras}
