import sys
import types
import unittest
import io

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

    def test_mux_sensor_record_and_pin_annotations(self):
        sensor = {'type': 'sht30', 'name': 'Bay sensor', 'note': 'Bay 1',
                  'pins': {'SDA': 6, 'SCL': 7, 'VCC': 36, 'GND': 8},
                  'bus': 'mux:3:0', 'address': 68}
        record = app.device_record(sensor, '7')
        self.assertEqual(record['bus'], 'mux:3:0')
        app.config['devices'].append(record)
        self.assertFalse(any(item['id'] == '7' for item in app.connections_for_header(6)))
        self.assertTrue(any(item['id'] == '7' for item in app.connections_for_header(36)))

    def test_live_output_endpoint(self):
        class FakePin:
            state = 0

            def value(self, value=None):
                if value is not None:
                    self.state = value
                return self.state

        class FakeClient:
            def __init__(self, request):
                self.source = io.BytesIO(request)
                self.output = io.BytesIO()

            def readline(self):
                return self.source.readline()

            def read(self, count):
                return self.source.read(count)

            def write(self, data):
                self.output.write(data)

        app.config['pins']['14'] = {'mode': 'output', 'value': 0, 'note': 'Desk LED'}
        old = app.pins.get(14)
        app.pins[14] = FakePin()
        try:
            body = b'{"value":1}'
            client = FakeClient(b'PUT /api/pins/14/value HTTP/1.1\r\nContent-Length: 11\r\n\r\n' + body)
            app.handle(client)
            response = client.output.getvalue()
            self.assertIn(b'200 OK', response)
            self.assertIn(b'"value": 1', response)
        finally:
            if old is None:
                app.pins.pop(14)
            else:
                app.pins[14] = old


if __name__ == '__main__':
    unittest.main()
