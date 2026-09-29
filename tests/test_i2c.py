import sys
import types
import unittest

sys.modules.setdefault('machine', types.SimpleNamespace())
sys.modules.setdefault('network', types.SimpleNamespace())
import app
import devices


class FakeBus:
    def __init__(self):
        self.writes = []

    def writeto(self, address, data):
        self.writes.append((address, data))


class I2cRoutingTests(unittest.TestCase):
    def setUp(self):
        self.previous_config = app.config
        self.previous_buses = devices.shared_buses.copy()
        self.bus = FakeBus()
        devices.shared_buses.clear()
        devices.shared_buses[4] = self.bus
        app.config = {'pins': {}, 'devices': [
            {'id': '3', 'type': 'tca9548a', 'name': 'Greenhouse mux',
             'pins': {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8},
             'address': 112,
             'channels': [{'name': 'Bay %d' % i, 'note': ''} for i in range(8)]}]}

    def tearDown(self):
        app.config = self.previous_config
        devices.shared_buses.clear()
        devices.shared_buses.update(self.previous_buses)

    def test_channel_path_selects_one_channel(self):
        paths = app.i2c_paths()
        self.assertEqual(len(paths), 9)
        self.assertEqual(paths[3]['name'], 'Greenhouse mux · Bay 2 (SD2 / SC2)')
        self.assertIs(app.i2c_bus('mux:3:2'), self.bus)
        self.assertEqual(self.bus.writes, [(112, b'\x00'), (112, b'\x04')])

    def test_direct_path_disables_channels(self):
        self.assertIs(app.i2c_bus('direct:4'), self.bus)
        self.assertEqual(self.bus.writes, [(112, b'\x00')])

    def test_invalid_path_rejected(self):
        with self.assertRaisesRegex(ValueError, '0–7'):
            app.i2c_bus('mux:3:8')


if __name__ == '__main__':
    unittest.main()
