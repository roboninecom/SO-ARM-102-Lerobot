# SPDX-License-Identifier: Apache-2.0
# Bus initialization adapted from LeRobot's FeetechMotorsBus.
from typing import TYPE_CHECKING

from lerobot.motors import Motor, MotorCalibration
from lerobot.motors.feetech.feetech import FeetechMotorsBus, patch_setPacketTimeout
from lerobot.motors.motors_bus import SerialMotorsBus
from lerobot.utils.import_utils import _feetech_sdk_available, require_package

if TYPE_CHECKING or _feetech_sdk_available:
    import scservo_sdk as scs

require_package("feetech-servo-sdk", extra="feetech", import_name="scservo_sdk")


class _PortHandler(scs.PortHandler):
    def setPacketTimeout(self, packet_length: int) -> None:  # noqa: N802
        patch_setPacketTimeout(self, packet_length)


class SOArm102FeetechBus(FeetechMotorsBus):
    """Strict model validation with package-local STS3235 tables, without global patches."""

    model_number_table = {**FeetechMotorsBus.model_number_table, "sts3235": 2057}
    model_ctrl_table = {
        **FeetechMotorsBus.model_ctrl_table,
        "sts3235": FeetechMotorsBus.model_ctrl_table["sts3215"],
    }
    model_encoding_table = {
        **FeetechMotorsBus.model_encoding_table,
        "sts3235": FeetechMotorsBus.model_encoding_table["sts3215"],
    }
    model_resolution_table = {**FeetechMotorsBus.model_resolution_table, "sts3235": 4096}
    model_baudrate_table = {
        **FeetechMotorsBus.model_baudrate_table,
        "sts3235": FeetechMotorsBus.model_baudrate_table["sts3215"],
    }
    port_handler_class = _PortHandler

    def __init__(
        self, port: str, motors: dict[str, Motor], calibration: dict[str, MotorCalibration] | None = None
    ):
        # The upstream constructor consults a module-global protocol table. Initialize
        # its serial base directly to keep STS3235 registration local to this subclass.
        if any(motor.model not in ("sts3215", "sts3235", "sts3250") for motor in motors.values()):
            raise ValueError("SO-ARM 102 requires STS3215, STS3235 or STS3250 motors.")
        SerialMotorsBus.__init__(self, port, motors, calibration)
        self.protocol_version = 0
        self.port_handler = self.port_handler_class(port)
        self.packet_handler = scs.PacketHandler(0)
        self.sync_reader = scs.GroupSyncRead(self.port_handler, self.packet_handler, 0, 0)
        self.sync_writer = scs.GroupSyncWrite(self.port_handler, self.packet_handler, 0, 0)
        self._comm_success = scs.COMM_SUCCESS
        self._no_error = 0

    def disconnect(self, disable_torque: bool = True) -> None:
        """Release the port even when a motor reports an error while disabling torque."""
        if self.is_connected:
            try:
                super().disconnect(disable_torque)
            finally:
                self.port_handler.closePort()
