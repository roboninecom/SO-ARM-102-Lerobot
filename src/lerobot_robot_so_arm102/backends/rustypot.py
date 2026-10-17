# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from lerobot.motors.motors_bus import SerialMotorsBus

if TYPE_CHECKING:
    import rustypot


class SOArm102RustypotBus(SerialMotorsBus):
    """STS3235 support for the Rustypot-backed LeRobot bus.

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
