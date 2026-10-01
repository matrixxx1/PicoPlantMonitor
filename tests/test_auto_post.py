import sys
import types
import unittest

sys.modules.setdefault('machine', types.SimpleNamespace())
sys.modules.setdefault('network', types.SimpleNamespace())
import auto_post
import app


class AutoPostTests(unittest.TestCase):
    def setUp(self):
        auto_post.last_attempt.clear()

    def test_settings_default_off_and_validate(self):
        self.assertEqual(auto_post.settings({}, 'sht30'),
                         {'enabled': False, 'interval_minutes': 1, 'url': ''})
        with self.assertRaises(ValueError):
            auto_post.settings({'auto_post': {'enabled': True, 'interval_minutes': 2,
                                               'url': 'https://example.com/x'}}, 'sht30')
        with self.assertRaises(ValueError):
            auto_post.settings({'auto_post': {'enabled': True}}, 'led')

    def test_placeholder_encoding_and_missing_value(self):
        self.assertEqual(auto_post.destination('https://host/a?temperature_c={temperature_c}&label={label}',
                                               {'temperature_c': -2.5, 'label': 'a & b'}),
                         'https://host/a?temperature_c=-2.5&label=a%20%26%20b')
        with self.assertRaises(ValueError):
            auto_post.destination('https://host/a?humidity_percent={humidity_percent}', {'temperature_c': 20})

    def test_schedule_interval_and_failed_reading(self):
        original_ticks_diff = getattr(auto_post.time, 'ticks_diff', None)
        auto_post.time.ticks_diff = lambda current, previous: current - previous
        self.addCleanup(lambda: setattr(auto_post.time, 'ticks_diff', original_ticks_diff)
                        if original_ticks_diff else delattr(auto_post.time, 'ticks_diff'))
        device = {'id': '1', 'type': 'sht30', 'auto_post': {'enabled': True,
                  'interval_minutes': 60, 'url': 'http://host/x?temperature_c={temperature_c}'}}
        sent = []
        read = lambda _: {'temperature_c': 21.5}
        auto_post.check([device], read, True, now=0, sender=sent.append)
        auto_post.check([device], read, True, now=59999, sender=sent.append)
        self.assertEqual(sent, [])
        auto_post.check([device], read, True, now=3600000, sender=sent.append)
        self.assertEqual(sent, ['http://host/x?temperature_c=21.5'])
        auto_post.check([device], lambda _: {'error': 'disconnected'}, True,
                        now=7200000, sender=sent.append)
        self.assertEqual(len(sent), 1)

    def test_device_record_persists_settings(self):
        record = app.device_record({'type': 'pir', 'name': 'motion', 'pins':
                                   {'SIGNAL': 16, 'VCC': 36, 'GND': 18}}, '4')
        self.assertFalse(record['auto_post']['enabled'])


if __name__ == '__main__':
    unittest.main()
