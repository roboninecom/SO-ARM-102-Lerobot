# SPDX-License-Identifier: Apache-2.0
from types import SimpleNamespace

import pytest
from lerobot.motors.feetech import FeetechMotorsBus
from lerobot.motors.feetech.tables import MODEL_NUMBER_TABLE, MODEL_PROTOCOL

from lerobot_robot_so_arm102.controller import make_motors

try:
    import scservo_sdk as scs

    from lerobot_robot_so_arm102.backends.feetech import SOArm102FeetechBus
except ImportError:
    pytest.skip("Legacy Feetech dependencies are not installed", allow_module_level=True)


class MemoryPort(scs.PortHandler):
    """In-memory serial peer: run the actual SDK framing and bus logic without a device."""

    def __init__(self, port):
        super().__init__(port)
        self.ser = SimpleNamespace(timeout=0)
        self.reply = []
        self.registers = {}
        self.error = 0
        for id_, model in enumerate((2057, 2825, 2825, 2057, 777, 777), 1):
            registers = bytearray(256)
            registers[0:2] = bytes([3, 1])
            registers[3:5] = model.to_bytes(2, "little")
            self.registers[id_] = registers

    def openPort(self):  # noqa: N802
        self.is_open = True
        return True

    def closePort(self):  # noqa: N802
        self.is_open = False

    def setBaudRate(self, baudrate):  # noqa: N802
        self.baudrate = baudrate
        return True

    def clearPort(self):  # noqa: N802
        self.reply = []

    def isPacketTimeout(self):  # noqa: N802
        return not self.reply

    def readPort(self, length):  # noqa: N802
        data, self.reply = self.reply[:length], self.reply[length:]
        return data

    def writePort(self, packet):  # noqa: N802
        id_, instruction, params = packet[2], packet[4], packet[5:-1]
        ids = list(self.registers) if id_ == 254 else [id_]
        for motor_id in ids:
            if motor_id not in self.registers:
                continue
            registers = self.registers[motor_id]
            data = []
            if instruction == 2:
                address, length = params
                data = list(registers[address : address + length])
            elif instruction == 3:
                address, *values = params
                registers[address : address + len(values)] = bytes(values)
                if address == 5:
                    self.registers[values[0]] = self.registers.pop(motor_id)
            elif instruction != 1:
                raise AssertionError(f"Unexpected instruction {instruction}")
            status = [motor_id, len(data) + 2, self.error, *data]
            self.reply.extend([255, 255, *status, (~sum(status)) & 255])
        return len(packet)


class SimulatedBus(SOArm102FeetechBus):
    port_handler_class = MemoryPort


@pytest.fixture
def bus():
    bus = SimulatedBus("memory", make_motors(True))
    yield bus
    bus.disconnect(disable_torque=False)


def test_mixed_models_connect_without_global_registration(bus):
    tables_before = (
        MODEL_NUMBER_TABLE.copy(),
        MODEL_PROTOCOL.copy(),
        FeetechMotorsBus.model_number_table.copy(),
    )
    bus.connect()
    assert bus.ping(1) == 2057
    assert bus.is_connected
    assert (MODEL_NUMBER_TABLE, MODEL_PROTOCOL, FeetechMotorsBus.model_number_table) == tables_before
    assert "sts3235" not in MODEL_NUMBER_TABLE


@pytest.mark.parametrize("model", [777, 9999, 1284])
def test_wrong_model_is_rejected(bus, model):
    bus.port_handler.registers[1][3:5] = model.to_bytes(2, "little")
    with pytest.raises(RuntimeError, match="incorrect model"):
        bus.connect()


def test_missing_motor_is_rejected(bus):
    del bus.port_handler.registers[6]
    with pytest.raises(RuntimeError, match="Missing motor"):
        bus.connect()


def test_firmware_must_match_across_models(bus):
    bus.port_handler.registers[2][1] = 2
    with pytest.raises(RuntimeError, match="different firmware"):
        bus.connect()


def test_setup_sts3235_and_calibration(bus, calibration):
    port = bus.port_handler
    port.registers = {42: port.registers[1]}
    bus.setup_motor("shoulder_pan", initial_baudrate=57600)
    assert set(port.registers) == {1}
    assert port.registers[1][5] == 1
    assert port.registers[1][6] == 0
    bus.write_calibration({"shoulder_pan": calibration["shoulder_pan"]})
    assert int.from_bytes(port.registers[1][9:11], "little") == 100
    assert int.from_bytes(port.registers[1][11:13], "little") == 4000


@pytest.mark.parametrize("position, normalized", [(100, 100.0), (2050, 50.0), (4000, 0.0)])
def test_gripper_inversion_round_trip(bus, calibration, position, normalized):
    bus.calibration = calibration
    assert bus._normalize({6: position}) == {6: normalized}
    assert bus._unnormalize({6: normalized}) == {6: position}


def test_disconnect_releases_port_after_motor_error(bus):
    bus.connect()
    bus.port_handler.error = 1
    with pytest.raises(RuntimeError, match="voltage"):
        bus.disconnect()
    assert not bus.is_connected
