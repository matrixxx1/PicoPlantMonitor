import gc
import json
import machine
import network
import os
import socket
import time
import devices
import auto_post

CONFIG = 'config.json'
GPIO = list(range(23)) + [26, 27, 28]
PHYSICAL = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10,
            8: 11, 9: 12, 10: 14, 11: 15, 12: 16, 13: 17, 14: 19,
            15: 20, 16: 21, 17: 22, 18: 24, 19: 25, 20: 26, 21: 27,
            22: 29, 26: 31, 27: 32, 28: 34}
HEADER_LABELS = ('GP0', 'GP1', 'GND', 'GP2', 'GP3', 'GP4', 'GP5', 'GND',
                 'GP6', 'GP7', 'GP8', 'GP9', 'GND', 'GP10', 'GP11', 'GP12',
                 'GP13', 'GND', 'GP14', 'GP15', 'GP16', 'GP17', 'GND',
                 'GP18', 'GP19', 'GP20', 'GP21', 'GND', 'GP22', 'RUN',
                 'GP26', 'GP27', 'AGND', 'GP28', 'ADC_VREF', '3V3(OUT)',
                 '3V3_EN', 'GND', 'VSYS', 'VBUS')
AP_NAME = 'PlantMontitor'
AP_IP = '192.168.4.1'
pins = {}
buses = {}
station = None
access_point = None
config = {'wifi': {}, 'pins': {}, 'devices': [], 'next_device_id': 1}


def load():
    global config
    try:
        with open(CONFIG) as f:
            value = json.load(f)
        if isinstance(value, dict) and isinstance(value.get('pins'), dict):
            config = value
            if not isinstance(config.get('devices'), list):
                config['devices'] = []
            config.setdefault('next_device_id', 1)
    except (OSError, ValueError):
        pass


def save():
    with open(CONFIG + '.tmp', 'w') as f:
        json.dump(config, f)
    try:
        os.remove(CONFIG)
    except OSError:
        pass
    os.rename(CONFIG + '.tmp', CONFIG)


def pin_config(n):
    return config['pins'].get(str(n), {'mode': 'unused', 'note': ''})


def i2c_pair(n):
    # RP2350 alternate I2C pin function: SDA on even GPIO, SCL on next GPIO.
    if n % 2 or n + 1 not in GPIO:
        return None
    return (n // 2) % 2, n + 1


def apply_pin(n):
    p = pin_config(n)
    mode = p.get('mode', 'unused')
    old = pins.pop(n, None)
    if old and hasattr(old, 'deinit'):
        old.deinit()
    buses.pop(n, None)
    if mode in ('input', 'button', 'digital_sensor'):
        pull = {'up': machine.Pin.PULL_UP, 'down': machine.Pin.PULL_DOWN}.get(p.get('pull'))
        pins[n] = machine.Pin(n, machine.Pin.IN, pull)
    elif mode == 'output':
        pins[n] = machine.Pin(n, machine.Pin.OUT, value=int(p.get('value', 0)))
    elif mode == 'analog':
        pins[n] = machine.ADC(n)
    elif mode == 'pwm':
        pwm = machine.PWM(machine.Pin(n))
        pwm.freq(int(p.get('frequency', 1000)))
        pwm.duty_u16(int(p.get('duty', 0)))
        pins[n] = pwm
    elif mode in ('i2c', 'tmp102'):
        pair = i2c_pair(n)
        if pair:
            bus, scl = pair
            buses[n] = machine.I2C(bus, sda=machine.Pin(n), scl=machine.Pin(scl), freq=100000)


def read_pin(n):
    p = pin_config(n)
    mode = p.get('mode', 'unused')
    result = {'pin': n, 'physical_pin': PHYSICAL[n], 'note': p.get('note', ''),
              'configuration': p, 'value': None, 'unit': None}
    result['devices'] = connections_for_header(PHYSICAL[n])
    try:
        if mode in ('input', 'button', 'digital_sensor', 'output'):
            result['value'] = pins[n].value()
        elif mode == 'analog':
            raw = pins[n].read_u16()
            result['value'] = raw
            result['unit'] = 'raw_u16'
            result['volts'] = round(raw * 3.3 / 65535, 4)
        elif mode == 'pwm':
            result['value'] = int(p.get('duty', 0))
            result['unit'] = 'duty_u16'
        elif mode == 'i2c':
            result['value'] = buses[n].scan()
            result['unit'] = 'device_addresses'
        elif mode == 'tmp102':
            raw = buses[n].readfrom_mem(int(p.get('address', 72)), 0, 2)
            signed = (raw[0] << 4) | (raw[1] >> 4)
            if signed & 0x800:
                signed -= 4096
            result['value'] = signed * 0.0625
            result['unit'] = 'celsius'
    except Exception as exc:
        result['error'] = str(exc)
    if result['devices']:
        result['device_readings'] = [
            {'id': item['id'], 'reading': devices.reading(device_by_id(item['id']))}
            for item in result['devices']]
        if result['value'] is None and len(result['device_readings']) == 1:
            result['value'] = result['device_readings'][0]['reading']
    return result


def connections_for_header(header):
    attached = []
    for device in config['devices']:
        for role, physical in device['pins'].items():
            if role in ('SDA', 'SCL') and str(device.get('bus', '')).startswith('mux:'):
                continue
            if int(physical) == header:
                attached.append({'id': device['id'], 'name': device['name'],
                                 'type': device['type'], 'role': role})
    return attached


def header_view():
    return [{'physical_pin': number, 'label': label,
             'gpio': devices.HEADER_TO_GPIO.get(number),
             'devices': connections_for_header(number)}
            for number, label in enumerate(HEADER_LABELS, 1)]


def device_by_id(ident):
    for device in config['devices']:
        if device['id'] == ident:
            return device
    return None


def device_record(value, ident):
    record = {'id': ident, 'type': value['type'], 'name': str(value['name']),
              'note': str(value.get('note', '')),
              'pins': {key: int(pin) for key, pin in value['pins'].items()},
              'address': devices.address_of(value) if 'SDA' in value['pins'] else None}
    if value['type'] == 'tca9548a':
        record['channels'] = [{'name': str(item.get('name', '')),
                               'note': str(item.get('note', ''))}
                              for item in value['channels']]
    elif value['type'] in ('sht30', 'tmp102'):
        record['bus'] = devices.bus_of(value)
    if value['type'] in auto_post.SENSOR_TYPES:
        record['auto_post'] = auto_post.settings(value, value['type'])
    else:
        auto_post.settings(value, value['type'])
    return record


def i2c_paths():
    paths = []
    seen = set()
    for item in config['devices']:
        if 'SDA' not in item['pins']:
            continue
        sda = devices.gpio_of(item, 'SDA')
        if sda not in seen:
            paths.append({'id': 'direct:%d' % sda, 'name': 'Pico GP%d / GP%d' % (sda, sda + 1)})
            seen.add(sda)
        if item['type'] == 'tca9548a':
            for channel, info in enumerate(item['channels']):
                name = info.get('name') or 'Channel %d' % channel
                paths.append({'id': 'mux:%s:%d' % (item['id'], channel),
                              'name': '%s · %s (SD%d / SC%d)' % (item['name'], name, channel, channel)})
    for sda in buses:
        if sda not in seen:
            paths.append({'id': 'direct:%d' % sda, 'name': 'Pico GP%d / GP%d' % (sda, sda + 1)})
    return paths


def i2c_bus(path):
    parts = str(path).split(':')
    if len(parts) == 2 and parts[0] == 'direct':
        sda = int(parts[1])
        bus = devices.shared_buses.get(sda) or buses.get(sda)
        if bus is None:
            raise ValueError('I²C bus is not configured')
        for item in config['devices']:
            if item['type'] == 'tca9548a' and devices.gpio_of(item, 'SDA') == sda:
                bus.writeto(devices.address_of(item), b'\x00')
        return bus
    if len(parts) == 3 and parts[0] == 'mux':
        item = device_by_id(parts[1])
        if item is None or item['type'] != 'tca9548a':
            raise ValueError('Multiplexer not found')
        channel = int(parts[2])
        if not 0 <= channel < 8:
            raise ValueError('Channel must be 0–7')
        sda = devices.gpio_of(item, 'SDA')
        bus = devices.shared_buses.get(sda)
        if bus is None:
            raise ValueError('I²C bus is not ready')
        for other in config['devices']:
            if other['type'] == 'tca9548a' and devices.gpio_of(other, 'SDA') == sda:
                bus.writeto(devices.address_of(other), b'\x00')
        bus.writeto(devices.address_of(item), bytes((1 << channel,)))
        return bus
    raise ValueError('Choose a configured I²C bus or channel')


def i2c_request(value):
    if not isinstance(value, dict):
        raise ValueError('Invalid I²C request')
    address = int(value.get('address', -1))
    if not 8 <= address <= 119:
        raise ValueError('I²C address must be 8–119')
    register = value.get('register')
    if register is not None:
        register = int(register)
        if not 0 <= register <= 255:
            raise ValueError('Register must be 0–255')
    return address, register


def wifi_settings(value, current):
    if not isinstance(value, dict):
        raise ValueError('Invalid Wi-Fi settings')
    ssid = str(value.get('ssid', ''))
    password = str(value.get('password', ''))
    if not 1 <= len(ssid.encode()) <= 32 or len(password) > 63:
        raise ValueError('Invalid Wi-Fi credentials')
    if value.get('open_network'):
        password = ''
    elif not password and ssid == current.get('ssid'):
        password = current.get('password', '')
    return {'ssid': ssid, 'password': password}


def save_and_reboot(client, result):
    save()
    send_json(client, '200 OK', result)
    time.sleep(0.5)
    machine.reset()


def start_ap():
    global access_point
    access_point = network.WLAN(network.AP_IF)
    access_point.active(True)
    access_point.config(essid=AP_NAME, security=network.WLAN.SEC_OPEN)
    print('Setup AP:', AP_NAME, AP_IP)


def connect_wifi():
    global station
    wifi = config.get('wifi', {})
    if not wifi.get('ssid'):
        start_ap()
        return
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(wifi['ssid'], wifi.get('password', ''))
    for _ in range(30):
        if station.isconnected():
            print('LAN IP:', station.ifconfig()[0])
            return
        time.sleep(0.5)
    start_ap()


def response(client, status, body, mime='application/json'):
    if not isinstance(body, bytes):
        body = body.encode()
    client.write(('HTTP/1.1 %s\r\nContent-Type: %s; charset=utf-8\r\n'
                  'Content-Length: %d\r\nConnection: close\r\n'
                  'Cache-Control: no-store\r\n\r\n' % (status, mime, len(body))).encode())
    client.write(body)


def send_json(client, status, obj):
    response(client, status, json.dumps(obj))


def captive_dns_reply(packet):
    # Answer ordinary IPv4 questions with the Pico AP address. Other record
    # types get an empty answer so clients can fall back to IPv4.
    if len(packet) < 17 or packet[2] & 0x80 or packet[4:6] != b'\x00\x01':
        return None
    end = 12
    while end < len(packet) and packet[end]:
        size = packet[end]
        if size & 0xc0 or end + size + 1 >= len(packet):
            return None
        end += size + 1
    if end + 5 > len(packet):
        return None
    question = packet[12:end + 5]
    is_ipv4 = packet[end + 1:end + 5] == b'\x00\x01\x00\x01'
    flags = b'\x81\x80'
    counts = b'\x00\x01\x00\x01\x00\x00\x00\x00' if is_ipv4 else b'\x00\x01\x00\x00\x00\x00\x00\x00'
    reply = packet[:2] + flags + counts + question
    if is_ipv4:
        reply += b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x1e\x00\x04'
        reply += bytes(int(octet) for octet in AP_IP.split('.'))
    return reply


def validate_pin(n, p):
    if n not in GPIO or not isinstance(p, dict):
        raise ValueError('Invalid GPIO or configuration')
    mode = p.get('mode', 'unused')
    if mode not in ('unused', 'input', 'button', 'digital_sensor', 'output',
                    'analog', 'pwm', 'i2c', 'tmp102'):
        raise ValueError('Unsupported mode')
    for other in GPIO:
        if other != n and pin_config(other).get('mode') in ('i2c', 'tmp102'):
            if i2c_pair(other)[1] == n:
                raise ValueError('GPIO is reserved as an I2C SCL pin')
    if mode == 'analog' and n not in (26, 27, 28):
        raise ValueError('Analog input requires GP26, GP27, or GP28')
    if mode in ('i2c', 'tmp102'):
        pair = i2c_pair(n)
        if not pair:
            raise ValueError('Select an even SDA GPIO with an available next SCL GPIO')
        scl = pair[1]
        if pin_config(scl).get('mode', 'unused') != 'unused':
            raise ValueError('SCL GPIO is already configured')
        for other in GPIO:
            if other != n and pin_config(other).get('mode') in ('i2c', 'tmp102'):
                if i2c_pair(other)[0] == pair[0]:
                    raise ValueError('I2C controller already in use')
    if mode == 'tmp102' and not 72 <= int(p.get('address', 72)) <= 75:
        raise ValueError('TMP102 address must be 72 to 75')
    if mode == 'pwm':
        if not 1 <= int(p.get('frequency', 1000)) <= 1000000:
            raise ValueError('PWM frequency outside range')
        if not 0 <= int(p.get('duty', 0)) <= 65535:
            raise ValueError('PWM duty outside range')
    if mode == 'output' and int(p.get('value', 0)) not in (0, 1):
        raise ValueError('Output must be 0 or 1')
    if len(str(p.get('note', ''))) > 120:
        raise ValueError('Note too long')


def handle(client):
    line = client.readline().decode().strip().split(' ')
    if len(line) < 2:
        return
    method, path = line[:2]
    length = 0
    host = ''
    while True:
        header = client.readline()
        if not header or header == b'\r\n':
            break
        if header.lower().startswith(b'content-length:'):
            length = int(header.split(b':', 1)[1])
        elif header.lower().startswith(b'host:'):
            host = header.split(b':', 1)[1].strip().decode().lower()
    if length > 2048:
        send_json(client, '413 Payload Too Large', {'error': 'Request too large'})
        return
    body = b''
    while len(body) < length:
        part = client.read(length - len(body))
        if not part:
            break
        body += part
    if method == 'GET' and access_point and access_point.active() and host and host not in (AP_IP, AP_IP + ':80') and not path.startswith('/api/'):
        client.write(('HTTP/1.1 302 Found\r\nLocation: http://%s/\r\n'
                      'Content-Length: 0\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n' % AP_IP).encode())
    elif path == '/':
        with open('index.html', 'rb') as f:
            response(client, '200 OK', f.read(), 'text/html')
    elif path == '/ui.js':
        with open('ui.js', 'rb') as f:
            response(client, '200 OK', f.read(), 'application/javascript')
    elif path == '/api-docs.js':
        with open('api-docs.js', 'rb') as f:
            response(client, '200 OK', f.read(), 'application/javascript')
    elif path == '/api/status' and method == 'GET':
        send_json(client, '200 OK', {'connected': bool(station and station.isconnected()),
                  'ip': station.ifconfig()[0] if station and station.isconnected() else AP_IP,
                  'ssid': config.get('wifi', {}).get('ssid', ''),
                  'setup_ap': bool(access_point and access_point.active())})
    elif path == '/api/reboot' and method == 'POST':
        send_json(client, '200 OK', {'rebooting': True})
        time.sleep(0.5)
        machine.reset()
    elif path == '/api/pins' and method == 'GET':
        send_json(client, '200 OK', [read_pin(n) for n in GPIO])
    elif path == '/api/header' and method == 'GET':
        send_json(client, '200 OK', header_view())
    elif path == '/api/catalog' and method == 'GET':
        send_json(client, '200 OK', devices.CATALOG)
    elif path == '/api/i2c/buses' and method == 'GET':
        send_json(client, '200 OK', i2c_paths())
    elif path in ('/api/i2c/scan', '/api/i2c/read', '/api/i2c/write') and method == 'POST':
        try:
            request = json.loads(body)
            bus = i2c_bus(request.get('bus'))
            if path.endswith('/scan'):
                result = {'addresses': bus.scan()}
            else:
                address, register = i2c_request(request)
                if path.endswith('/read'):
                    count = int(request.get('count', 1))
                    if not 1 <= count <= 32:
                        raise ValueError('Read length must be 1–32 bytes')
                    data = bus.readfrom_mem(address, register, count) if register is not None else bus.readfrom(address, count)
                    result = {'address': address, 'register': register,
                              'data': list(data), 'hex': ''.join('%02X' % byte for byte in data)}
                else:
                    raw = request.get('data')
                    if not isinstance(raw, list) or not 1 <= len(raw) <= 32 or any(not isinstance(byte, int) or not 0 <= byte <= 255 for byte in raw):
                        raise ValueError('Write 1–32 data bytes (0–255)')
                    data = bytes(raw)
                    count = bus.writeto_mem(address, register, data) if register is not None else bus.writeto(address, data)
                    result = {'address': address, 'register': register, 'written': count}
            send_json(client, '200 OK', result)
        except (ValueError, TypeError, KeyError, OSError) as exc:
            send_json(client, '400 Bad Request', {'error': str(exc)})
    elif path == '/api/devices' and method == 'GET':
        send_json(client, '200 OK', [devices.view(item) for item in config['devices']])
    elif path == '/api/devices' and method == 'POST':
        try:
            new = json.loads(body)
            devices.validate(new, config['devices'], config['pins'])
            new = device_record(new, str(config['next_device_id']))
            config['devices'].append(new)
            config['next_device_id'] += 1
            save_and_reboot(client, {'saved': True, 'rebooting': True, 'id': new['id']})
        except (ValueError, TypeError, KeyError) as exc:
            send_json(client, '400 Bad Request', {'error': str(exc)})
    elif path.startswith('/api/devices/'):
        parts = path.split('/')
        ident = parts[3] if len(parts) > 3 else ''
        item = device_by_id(ident)
        if item is None:
            send_json(client, '404 Not Found', {'error': 'Device not found'})
        elif len(parts) == 5 and parts[4] == 'value' and method == 'PUT':
            try:
                if item['type'] not in ('led', 'active_buzzer', 'relay_module'):
                    raise ValueError('This device has no controllable output')
                value = int(json.loads(body)['value'])
                if value not in (0, 1):
                    raise ValueError('Output must be 0 or 1')
                devices.instances[ident].value(value)
                devices.last_read.pop(ident, None)
                send_json(client, '200 OK', devices.view(item))
            except (ValueError, TypeError, KeyError) as exc:
                send_json(client, '400 Bad Request', {'error': str(exc)})
        elif len(parts) == 4 and method == 'GET':
            send_json(client, '200 OK', devices.view(item))
        elif len(parts) == 4 and method == 'DELETE':
            if any(str(other.get('bus', '')).startswith('mux:%s:' % ident)
                   for other in config['devices']):
                send_json(client, '400 Bad Request', {'error': 'Remove devices on this multiplexer first'})
                return
            config['devices'] = [device for device in config['devices'] if device['id'] != ident]
            save_and_reboot(client, {'deleted': True, 'rebooting': True})
        elif len(parts) == 4 and method == 'PUT':
            try:
                new = json.loads(body)
                new['id'] = ident
                devices.validate(new, config['devices'], config['pins'])
                replacement = device_record(new, ident)
                if replacement['type'] == 'tca9548a':
                    candidates = [replacement if device['id'] == ident else device
                                  for device in config['devices']]
                    for dependent in candidates:
                        if str(dependent.get('bus', '')).startswith('mux:%s:' % ident):
                            devices.validate(dependent, [item for item in candidates if item['id'] != dependent['id']], config['pins'])
                config['devices'] = [replacement if device['id'] == ident else device
                                     for device in config['devices']]
                save_and_reboot(client, {'saved': True, 'rebooting': True, 'id': ident})
            except (ValueError, TypeError, KeyError) as exc:
                send_json(client, '400 Bad Request', {'error': str(exc)})
        else:
            send_json(client, '405 Method Not Allowed', {'error': 'Method not allowed'})
    elif path.startswith('/api/pins/') and path.endswith('/note') and method == 'PUT':
        try:
            n = int(path.split('/')[3])
            if n not in GPIO:
                raise ValueError('Unavailable GPIO')
            note = str(json.loads(body)['note'])
            if len(note) > 120:
                raise ValueError('Note too long')
            config['pins'].setdefault(str(n), {'mode': 'unused'})['note'] = note
            save()
            send_json(client, '200 OK', read_pin(n))
        except (ValueError, TypeError, KeyError) as exc:
            send_json(client, '400 Bad Request', {'error': str(exc)})
    elif path.startswith('/api/pins/') and path.endswith('/value') and method == 'PUT':
        try:
            n = int(path.split('/')[3])
            if n not in GPIO or pin_config(n).get('mode') != 'output':
                raise ValueError('Pin must be configured as an output')
            value = int(json.loads(body)['value'])
            if value not in (0, 1):
                raise ValueError('Output value must be 0 or 1')
            pins[n].value(value)
            send_json(client, '200 OK', read_pin(n))
        except (ValueError, TypeError, KeyError) as exc:
            send_json(client, '400 Bad Request', {'error': str(exc)})
    elif path.startswith('/api/pins/'):
        try:
            n = int(path.split('/')[3])
            if n not in GPIO:
                raise ValueError('Unavailable GPIO')
            if method == 'GET':
                send_json(client, '200 OK', read_pin(n))
            elif method == 'PUT':
                new = json.loads(body)
                if connections_for_header(PHYSICAL[n]) and new.get('mode', 'unused') != 'unused':
                    raise ValueError('Remove the connected device before changing this GPIO mode')
                validate_pin(n, new)
                config['pins'][str(n)] = new
                save_and_reboot(client, {'saved': True, 'rebooting': True, 'pin': n})
            else:
                send_json(client, '405 Method Not Allowed', {'error': 'Method not allowed'})
        except (ValueError, TypeError) as exc:
            send_json(client, '400 Bad Request', {'error': str(exc)})
    elif path == '/api/wifi' and method == 'PUT':
        try:
            config['wifi'] = wifi_settings(json.loads(body), config.get('wifi', {}))
            save()
            send_json(client, '200 OK', {'saved': True, 'rebooting': True})
            time.sleep(0.5)
            machine.reset()
        except (ValueError, TypeError) as exc:
            send_json(client, '400 Bad Request', {'error': str(exc)})
    elif method == 'GET' and access_point and access_point.active():
        client.write(('HTTP/1.1 302 Found\r\nLocation: http://%s/\r\n'
                      'Content-Length: 0\r\nConnection: close\r\n\r\n' % AP_IP).encode())
    else:
        send_json(client, '404 Not Found', {'error': 'Not found'})


def run():
    load()
    for n in GPIO:
        try:
            apply_pin(n)
        except Exception as exc:
            print('Pin', n, 'configuration error:', exc)
    devices.setup(config['devices'])
    auto_post.last_attempt.clear()
    schedule_start = time.ticks_ms()
    for item in config['devices']:
        if item.get('auto_post', {}).get('enabled'):
            auto_post.last_attempt[item['id']] = schedule_start
    connect_wifi()
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 80))
    server.listen(2)
    server.settimeout(0.25)
    dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dns.bind(('0.0.0.0', 53))
    dns.settimeout(0.01)
    last_auto_check = time.ticks_ms()
    while True:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_auto_check) >= 60000:
            last_auto_check = now
            auto_post.check(config['devices'], devices.reading,
                            bool(station and station.isconnected()), now)
        if access_point and access_point.active():
            try:
                packet, address = dns.recvfrom(512)
                reply = captive_dns_reply(packet)
                if reply:
                    dns.sendto(reply, address)
            except OSError:
                pass
        try:
            client, _ = server.accept()
        except OSError:
            if station and config.get('wifi', {}).get('ssid'):
                if station.isconnected() and access_point and access_point.active():
                    access_point.active(False)
                elif not station.isconnected() and not (access_point and access_point.active()):
                    start_ap()
            continue
        try:
            client.settimeout(5)
            handle(client)
        except Exception as exc:
            print('Request error:', exc)
        finally:
            client.close()
            gc.collect()
