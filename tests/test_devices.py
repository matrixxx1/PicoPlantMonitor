import sys
import types
import unittest

sys.modules.setdefault('machine', types.SimpleNamespace())
import devices


def assignment(kind, pins, ident='1', address=None):
    value = {'id': ident, 'type': kind, 'name': kind, 'note': '', 'pins': pins}
    if address is not None:
        value['address'] = address
    return value


class DeviceValidationTests(unittest.TestCase):
    def test_physical_pin_map(self):
        self.assertEqual(devices.HEADER_TO_GPIO[6], 4)
        self.assertEqual(devices.HEADER_TO_GPIO[7], 5)
        self.assertEqual(devices.HEADER_TO_GPIO[31], 26)
        self.assertNotIn(36, devices.HEADER_TO_GPIO)

    def test_sht30_uses_gp4_gp5_and_power_ground(self):
        sensor = assignment('sht30', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8}, address=68)
        self.assertTrue(devices.validate(sensor, [], {}))
        sensor['pins']['SCL'] = 10
        with self.assertRaisesRegex(ValueError, 'SCL must'):
            devices.validate(sensor, [], {})

    def test_analog_sensor_only_uses_adc(self):
        sensor = assignment('soil_moisture', {'ANALOG': 6, 'VCC': 36, 'GND': 33})
        with self.assertRaisesRegex(ValueError, 'GP26'):
            devices.validate(sensor, [], {})

    def test_signal_conflict_but_shared_i2c_allowed(self):
        sensor = assignment('sht30', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8}, address=68)
        thermometer = assignment('tmp102', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8}, '2', 72)
        self.assertTrue(devices.validate(thermometer, [sensor], {}))
        led = assignment('led', {'SIGNAL': 6, 'GND': 8}, '3')
        with self.assertRaisesRegex(ValueError, 'already used'):
            devices.validate(led, [sensor], {})

    def test_sht30_crc_example(self):
        self.assertEqual(devices.crc8(bytes.fromhex('beef')), 0x92)

    def test_tca9548a_channels_and_shared_i2c(self):
        mux = assignment('tca9548a', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8}, address=112)
        mux['channels'] = [{'name': '', 'note': ''} for _ in range(8)]
        sensor = assignment('sht30', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 3}, '2', 68)
        self.assertTrue(devices.validate(mux, [sensor], {}))
        mux['address'] = 120
        with self.assertRaisesRegex(ValueError, '112–119'):
            devices.validate(mux, [sensor], {})
        mux['address'] = 112
        mux['channels'].pop()
        with self.assertRaisesRegex(ValueError, 'eight'):
            devices.validate(mux, [sensor], {})

    def test_same_address_on_separate_mux_channels(self):
        mux = assignment('tca9548a', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8}, '6', 112)
        mux['channels'] = [{'name': '', 'note': ''} for _ in range(8)]
        first = assignment('sht30', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8}, '7', 68)
        first['bus'] = 'mux:6:0'
        second = assignment('sht30', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8}, '8', 68)
        second['bus'] = 'mux:6:1'
        self.assertTrue(devices.validate(first, [mux], {}))
        self.assertTrue(devices.validate(second, [mux, first], {}))
        second['bus'] = 'mux:6:0'
        with self.assertRaisesRegex(ValueError, 'address already used'):
            devices.validate(second, [mux, first], {})
        second['bus'] = 'mux:6:8'
        with self.assertRaisesRegex(ValueError, 'channel 0–7'):
            devices.validate(second, [mux, first], {})

    def test_mux_sensor_selects_channel_before_read(self):
        class FakeBus:
            def __init__(self):
                self.writes = []

            def writeto(self, address, data):
                self.writes.append((address, data))

        mux = assignment('tca9548a', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8}, '6', 112)
        sensor = assignment('sht30', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8}, '7', 68)
        sensor['bus'] = 'mux:6:2'
        previous = devices.configured_devices[:]
        try:
            devices.configured_devices[:] = [mux, sensor]
            bus = FakeBus()
            devices.select_device_bus(sensor, bus)
            self.assertEqual(bus.writes, [(112, b'\x00'), (112, b'\x04')])
        finally:
            devices.configured_devices[:] = previous


if __name__ == '__main__':
    unittest.main()
