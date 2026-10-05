import sys
import types
import unittest

sys.modules.setdefault('machine', types.SimpleNamespace())
import devices


class ReadingTimeTests(unittest.TestCase):
    def test_time_of_reading_is_included(self):
        class FakePin:
            def value(self):
                return 1

        original_gmtime = devices.time.gmtime
        original_ticks_ms = getattr(devices.time, 'ticks_ms', None)
        devices.time.gmtime = lambda: (2026, 10, 1, 19, 42, 10, 3, 274)
        devices.time.ticks_ms = lambda: 1000
        devices.instances['clock-test'] = FakePin()
        devices.last_read.pop('clock-test', None)
        self.addCleanup(setattr, devices.time, 'gmtime', original_gmtime)
        self.addCleanup(lambda: setattr(devices.time, 'ticks_ms', original_ticks_ms)
                        if original_ticks_ms else delattr(devices.time, 'ticks_ms'))
        self.addCleanup(devices.instances.pop, 'clock-test', None)
        self.addCleanup(devices.last_read.pop, 'clock-test', None)

        result = devices.reading({'id': 'clock-test', 'type': 'pir'})

        self.assertEqual(result['value'], 1)
        self.assertEqual(result['time_of_reading'], '2026-10-01T19:42:10Z')


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

    def test_ssd1306_defaults_and_shared_i2c(self):
        display = assignment('ssd1306', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 38}, address=60)
        sensor = assignment('sht30', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8}, '2', 68)
        self.assertTrue(devices.validate(display, [sensor], {}))
        self.assertEqual(devices.CATALOG['ssd1306']['defaults'],
                         {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 38})
        self.assertEqual(devices.CATALOG['ssd1306']['wire_colors']['SCL'], 'yellow')
        display['address'] = 62
        with self.assertRaisesRegex(ValueError, '60 or 61'):
            devices.validate(display, [sensor], {})

    def test_oled_refresh_draws_status(self):
        class FakeDisplay:
            def __init__(self):
                self.lines = []
                self.shown = False

            def fill(self, value):
                self.lines = []

            def text(self, value, x, y, color):
                self.lines.append((value, x, y, color))

            def show(self):
                self.shown = True

        display = assignment('ssd1306', {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 38}, 'screen', 60)
        fake = FakeDisplay()
        previous_devices = devices.configured_devices[:]
        devices.configured_devices[:] = [display]
        devices.instances['screen'] = fake
        self.addCleanup(devices.configured_devices.__setitem__, slice(None), previous_devices)
        self.addCleanup(devices.instances.pop, 'screen', None)

        devices.refresh_displays('192.168.50.179')

        self.assertTrue(fake.shown)
        self.assertEqual(fake.lines[0][0], 'Pico Plant')
        self.assertEqual(fake.lines[1][0], 'Monitor')
        self.assertEqual(fake.lines[3][0], '192.168.50.179')
        self.assertEqual(devices.display_snapshot(), {
            'width': 128, 'height': 64,
            'lines': ['Pico Plant', 'Monitor', '', '192.168.50.179']})

    def test_oled_cycles_sensor_pages(self):
        sensors = [
            assignment('sht30', {'SDA': 1, 'SCL': 2, 'VCC': 36, 'GND': 38}, '1', 68),
            assignment('sht30', {'SDA': 4, 'SCL': 5, 'VCC': 36, 'GND': 18}, '2', 68),
        ]
        sensors[0]['note'] = 'Seed bay 1'
        sensors[1]['note'] = 'Seed bay 2'
        readings = {
            '1': {'temperature_c': 21.25, 'humidity_percent': 45.5},
            '2': {'temperature_c': 22.75, 'humidity_percent': 55.5},
        }
        original_reading = devices.reading
        original_devices = devices.configured_devices[:]
        original_index = devices.display_cycle_index
        original_step = devices.display_countdown_step
        devices.reading = lambda device: readings[device['id']]
        devices.configured_devices[:] = sensors
        devices.display_cycle_index = 0
        devices.display_countdown_step = 0
        self.addCleanup(setattr, devices, 'reading', original_reading)
        self.addCleanup(devices.configured_devices.__setitem__, slice(None), original_devices)
        self.addCleanup(setattr, devices, 'display_cycle_index', original_index)
        self.addCleanup(setattr, devices, 'display_countdown_step', original_step)

        first = devices._display_lines()
        for _ in range(4):
            last_first = devices._display_lines()
        second = devices._display_lines()
        for _ in range(4):
            devices._display_lines()
        third = devices._display_lines()

        self.assertEqual(first, ['Seed bay 1', '', '21.2C / 70.2F', 'Humidity 45.5%',
                                 '', '* Humidity low', '', 'Next [#####]'])
        self.assertEqual(last_first[-1], 'Next [#....]')
        self.assertEqual(second, ['Seed bay 2', '', '22.8C / 73.0F', 'Humidity 55.5%',
                                  '', 'Good', '', 'Next [#####]'])
        self.assertEqual(third, first)

    def test_reaper_display_reports_both_out_of_range_issues(self):
        sensor = assignment('sht30', {'SDA': 1, 'SCL': 2, 'VCC': 36, 'GND': 38}, '1', 68)
        sensor['note'] = 'Seed bay 1'
        original_reading = devices.reading
        original_devices = devices.configured_devices[:]
        original_index = devices.display_cycle_index
        original_step = devices.display_countdown_step
        devices.reading = lambda _: {'temperature_c': 33, 'humidity_percent': 45}
        devices.configured_devices[:] = [sensor]
        devices.display_cycle_index = devices.display_countdown_step = 0
        self.addCleanup(setattr, devices, 'reading', original_reading)
        self.addCleanup(devices.configured_devices.__setitem__, slice(None), original_devices)
        self.addCleanup(setattr, devices, 'display_cycle_index', original_index)
        self.addCleanup(setattr, devices, 'display_countdown_step', original_step)

        lines = devices._display_lines()

        self.assertEqual(lines[5], '* Temp high')
        self.assertEqual(lines[6], '* Humidity low')

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

    def test_separate_software_i2c_pairs_allow_same_address(self):
        first = assignment('sht30', {'SDA': 9, 'SCL': 10, 'VCC': 36, 'GND': 13}, '3', 68)
        second = assignment('sht30', {'SDA': 11, 'SCL': 12, 'VCC': 36, 'GND': 13}, '4', 68)
        self.assertTrue(devices.validate(second, [first], {}))

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
