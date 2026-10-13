# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from lerobot.motors.motors_bus import SerialMotorsBus
from lerobot.utils.import_utils import require_package

from ..config_so_arm102 import SOArm102FollowerConfig
from ..controller import make_motors
from .sts import STSController

if TYPE_CHECKING:
    import rustypot


class SOArm102RustypotBus(SerialMotorsBus):
    """Experimental adapter for LeRobot PR #4672 at 8d3511625da3.

    Preserve the exact STS3235 model number while sharing the STS register layout.
    Prefer Rustypot's own definition if a later version adds this model.
    """

    @staticmethod
    def _find_model(model: str) -> tuple[int, rustypot.ServoDefinition]:
        sdk = import_module("rustypot")
        if model == "sts3235" and sdk.find_model(model) is None:
            _, definition = SerialMotorsBus._find_model("sts3215")
            return 2057, definition
        return SerialMotorsBus._find_model(model)


def make_controller(config: SOArm102FollowerConfig) -> STSController:
    """Construct the experimental controller only with a compatible LeRobot bus API."""
    if not hasattr(SerialMotorsBus, "_find_model"):
        raise RuntimeError(
            "controller='rustypot' requires the Rustypot-backed LeRobot API. "
            "Use the tested PR #4672 revision documented in this package's README."
        )
    require_package("rustypot", extra="rustypot")
    return STSController(SOArm102RustypotBus(config.port, make_motors(config.use_degrees)), config)
