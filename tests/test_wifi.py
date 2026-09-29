import sys
import types
import unittest

sys.modules.setdefault('machine', types.SimpleNamespace())
sys.modules.setdefault('network', types.SimpleNamespace())
import app


class WifiSettingsTests(unittest.TestCase):
    def test_blank_password_preserves_current_network_password(self):
        saved = app.wifi_settings({'ssid': 'Home', 'password': ''},
                                  {'ssid': 'Home', 'password': 'saved-secret'})
        self.assertEqual(saved['password'], 'saved-secret')

    def test_new_network_and_explicit_open_network(self):
        current = {'ssid': 'Home', 'password': 'saved-secret'}
        self.assertEqual(app.wifi_settings({'ssid': 'Other', 'password': 'new-secret'}, current),
                         {'ssid': 'Other', 'password': 'new-secret'})
        self.assertEqual(app.wifi_settings({'ssid': 'Home', 'open_network': True}, current),
                         {'ssid': 'Home', 'password': ''})


if __name__ == '__main__':
    unittest.main()
