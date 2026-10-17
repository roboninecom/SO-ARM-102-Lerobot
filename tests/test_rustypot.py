# SPDX-License-Identifier: Apache-2.0
import pytest
from lerobot.motors.motors_bus import SerialMotorsBus

from lerobot_robot_so_arm102 import SOArm102FollowerConfig
from lerobot_robot_so_arm102.backends.rustypot import SOArm102RustypotBus
from lerobot_robot_so_arm102.backends.sts import STSController
from lerobot_robot_so_arm102.controller import make_motors

pytestmark = pytest.mark.skipif(
    not hasattr(SerialMotorsBus, "_find_model"), reason="Requires the Rustypot-backed LeRobot revision"
)


class MemoryBus:
    """Injected Rustypot transport; LeRobot uses actual installed servo definitions."""

    def __init__(self, port, baudrate, timeout, definitions):
        self.baudrate = baudrate
        self.registers = {
            id_: {"model_number": model, "firmware_major_version": 3, "firmware_minor_version": 1}
            for id_, model in enumerate((2057, 2825, 2825, 2057, 777, 777), 1)
        }

    def close(self):
        pass

    def read_register_with_error(self, id_, name, retries=0):
        if id_ not in self.registers:
            raise OSError("Motor missing")
        return self.registers[id_].get(name, 0), 0

    def write_register_with_error(self, id_, name, value, retries=0):
        self.registers[id_][name] = value
        return 0

    def sync_read_register_with_error(self, ids, name, retries=0):
        return [self.read_register_with_error(id_, name) for id_ in ids]

    def sync_write_register(self, ids, name, values, retries=0):
        for id_, value in zip(ids, values, strict=True):
            self.write_register_with_error(id_, name, value)

    def set_torque(self, ids, enabled, retries=0):
        for id_ in ids:
            self.registers[id_]["torque_enable"] = int(enabled)
        return {}

    def broadcast_scan(self, definition):
        return {id_: registers["model_number"] for id_, registers in self.registers.items()}

    def change_id(self, definition, initial_id, target_id):
        self.registers[target_id] = self.registers.pop(initial_id)

    def change_baudrate(self, definition, id_, baudrate):
        self.registers[id_]["baud_rate"] = baudrate

    def set_baudrate(self, baudrate):
        self.baudrate = baudrate


class SimulatedBus(SOArm102RustypotBus):
    def _open_bus(self):
        return MemoryBus(self.port, self.default_baudrate, self.default_timeout / 1000, self._definitions)


@pytest.fixture
def bus():
    bus = SimulatedBus("memory", make_motors(True))
    bus.connect(handshake=False)
    yield bus
    bus.disconnect(disable_torque=False)


def test_sts3235_definition_and_strict_handshake(bus):
    assert bus._model_number("sts3235") == 2057
    assert bus.resolution("sts3235") == 4096
    bus._handshake()
    bus._bus.registers[1]["model_number"] = 777
    with pytest.raises(RuntimeError, match="incorrect model"):
        bus._handshake()


def test_firmware_must_match(bus):
    bus._bus.registers[2]["firmware_minor_version"] = 2
    with pytest.raises(RuntimeError, match="different firmware"):
        bus._handshake()


def test_sts3235_setup(bus):
    bus._bus.registers = {42: bus._bus.registers[1]}
    bus.setup_motor("shoulder_pan", initial_baudrate=57600)
    assert set(bus._bus.registers) == {1}
    assert bus._bus.registers[1]["baud_rate"] == 1_000_000


def test_configuration_and_calibration(bus, calibration):
    controller = STSController(bus, SOArm102FollowerConfig(port="memory", controller="rustypot"))
    controller.configure()
    assert all(registers["torque_enable"] == 0 for registers in bus._bus.registers.values())
    assert all(registers["operating_mode"] == 0 for registers in bus._bus.registers.values())
    controller.apply_calibration(calibration)
    assert controller.is_calibrated(calibration)
    bus._bus.registers[6]["present_position"] = 100
    assert controller.read_positions()["gripper"] == 100.0
    controller.write_positions({"gripper": 0.0})
    assert bus._bus.registers[6]["goal_position"] == 4000
