"""Scheduled sensor readings sent as HTTP POST requests with URL values."""

import socket
import time

INTERVALS = (1, 60, 780, 1440)
SENSOR_TYPES = ('pir', 'soil_moisture', 'dht22', 'ds18b20', 'sht30', 'tmp102')
last_attempt = {}


def settings(value, kind):
    raw = value.get('auto_post') or {}
    if kind not in SENSOR_TYPES:
        if raw.get('enabled'):
            raise ValueError('Auto post is only available for sensors')
        return None
    enabled = raw.get('enabled', False)
    interval = raw.get('interval_minutes', 1)
    url = raw.get('url', '')
    if not isinstance(enabled, bool) or type(interval) is not int or interval not in INTERVALS:
        raise ValueError('Invalid auto post settings')
    if not isinstance(url, str) or len(url) > 512 or ('\r' in url or '\n' in url):
        raise ValueError('Invalid destination URL')
    if enabled and not url.startswith(('http://', 'https://')):
        raise ValueError('Auto post needs an HTTP or HTTPS URL')
    return {'enabled': enabled, 'interval_minutes': interval, 'url': url}


def encode(value):
    data = str(value).encode('utf-8')
    return ''.join(chr(byte) if (48 <= byte <= 57 or 65 <= byte <= 90 or
            97 <= byte <= 122 or byte in b'-._~') else '%%%02X' % byte for byte in data)


def destination(template, reading):
    if not isinstance(reading, dict) or reading.get('error') or not reading:
        raise ValueError('Sensor has no valid reading')
    result = template
    for name, value in reading.items():
        result = result.replace('{' + name + '}', encode(value))
    if '{' in result or '}' in result:
        raise ValueError('Destination has a placeholder without a sensor value')
    return result


def post(url):
    secure = url.startswith('https://')
    if not secure and not url.startswith('http://'):
        raise ValueError('Destination must use HTTP or HTTPS')
    rest = url[8 if secure else 7:]
    authority, slash, path = rest.partition('/')
    if not authority or '@' in authority or not slash:
        raise ValueError('Destination URL needs a host and path')
    host, colon, port_text = authority.rpartition(':')
    if not colon:
        host, port = authority, 443 if secure else 80
    else:
        port = int(port_text)
    if not host or not 1 <= port <= 65535 or any(c in host for c in ' /?#'):
        raise ValueError('Invalid destination host')
    address = socket.getaddrinfo(host, port)[0][-1]
    connection = socket.socket()
    try:
        connection.settimeout(5)
        connection.connect(address)
        if secure:
            import ssl
            connection = ssl.wrap_socket(connection, server_hostname=host)
            connection.settimeout(5)
        request = ('POST /%s HTTP/1.0\r\nHost: %s\r\nContent-Length: 0\r\n'
                   'Connection: close\r\n\r\n' % (path, authority))
        connection.write(request.encode()) if hasattr(connection, 'write') else connection.sendall(request.encode())
        status = connection.readline() if hasattr(connection, 'readline') else connection.recv(128).split(b'\r\n', 1)[0]
        if not status.startswith(b'HTTP/') or int(status.split()[1]) >= 400:
            raise OSError('Destination rejected POST: ' + status.decode().strip())
    finally:
        connection.close()


def check(all_devices, read, connected, now=None, sender=post):
    if not connected:
        return
    if now is None:
        now = time.ticks_ms()
    for device in all_devices:
        setting = device.get('auto_post') or {}
        if not setting.get('enabled') or device.get('type') not in SENSOR_TYPES:
            continue
        ident = device['id']
        interval_ms = setting['interval_minutes'] * 60000
        previous = last_attempt.get(ident)
        if previous is None:
            last_attempt[ident] = now
            continue
        if time.ticks_diff(now, previous) < interval_ms:
            continue
        last_attempt[ident] = now
        try:
            sender(destination(setting['url'], read(device)))
        except Exception as exc:
            print('Auto post', ident, 'failed:', exc)
