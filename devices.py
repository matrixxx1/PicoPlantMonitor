"""Supported physical devices, pin validation, and readings for Pico 2 W."""

import machine
import time

GPIO_TO_HEADER = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10,
                  8: 11, 9: 12, 10: 14, 11: 15, 12: 16, 13: 17, 14: 19,
                  15: 20, 16: 21, 17: 22, 18: 24, 19: 25, 20: 26,
                  21: 27, 22: 29, 26: 31, 27: 32, 28: 34}
HEADER_TO_GPIO = {header: gpio for gpio, header in GPIO_TO_HEADER.items()}
GROUNDS = (3, 8, 13, 18, 23, 28, 33, 38)
POWER = 36

CATALOG = {
    'button': {
        'name': 'Push button', 'category': 'Buttons',
        'description': 'Reads pressed or released using an internal pull-up.',
        'roles': [('SIGNAL', 'gpio'), ('GND', 'ground')],
        'wiring': 'Connect the switch between SIGNAL and GND. Pressed reads 0.',
        'resistor': None},
    'led': {
        'name': 'Single LED', 'category': 'Outputs',
        'description': 'Turns a small indicator LED on or off.',
        'roles': [('SIGNAL', 'gpio'), ('GND', 'ground')],
        'wiring': 'SIGNAL → resistor → LED anode (+); LED cathode (−) → GND.',
        'resistor': {'ohms': 330, 'bands': ['orange', 'orange', 'brown', 'gold'],
                     'placement': 'In series between SIGNAL and LED anode.'}},
    'active_buzzer': {
        'name': '3.3 V active buzzer module', 'category': 'Outputs',
        'description': 'Switches a low-current active buzzer module on or off.',
        'roles': [('SIGNAL', 'gpio'), ('VCC', 'power'), ('GND', 'ground')],
        'wiring': 'SIGNAL → module IN; 3V3 → module VCC; GND → module GND. Use a module rated for 3.3 V logic.',
        'resistor': None},
    'relay_module': {
        'name': '3.3 V relay module', 'category': 'Outputs',
        'description': 'Switches a relay module input; the GPIO never drives a bare relay coil.',
        'roles': [('SIGNAL', 'gpio'), ('VCC', 'power'), ('GND', 'ground')],
        'wiring': 'SIGNAL → module IN; 3V3 → module VCC; GND → module GND. Use a 3.3 V-compatible module with suitable external load wiring.',
        'resistor': None},
    'pir': {
        'name': '3.3 V PIR motion module', 'category': 'Sensors',
        'description': 'Reads a motion/no-motion digital output.',
        'roles': [('SIGNAL', 'gpio'), ('VCC', 'power'), ('GND', 'ground')],
        'wiring': 'Module OUT → SIGNAL; VCC → 3V3; GND → GND. Check that OUT never exceeds 3.3 V.',
        'resistor': None},
    'soil_moisture': {
        'name': 'Capacitive soil moisture sensor', 'category': 'Sensors',
        'description': 'Reads raw analog moisture voltage for later dry/wet calibration.',
        'roles': [('ANALOG', 'adc'), ('VCC', 'power'), ('GND', 'ground')],
        'wiring': 'Sensor analog OUT → GP26, GP27, or GP28; VCC → 3V3; GND → GND. Analog OUT must stay within 0–3.3 V.',
        'resistor': None},
    'dht22': {
        'name': 'DHT22 / AM2302', 'category': 'Sensors',
        'description': 'Digital air temperature and relative humidity.',
        'roles': [('DATA', 'gpio'), ('VCC', 'power'), ('GND', 'ground')],
        'wiring': 'DATA → GPIO; VCC → 3V3; GND → GND. Bare sensors need a pull-up from DATA to 3V3; many breakout boards include one.',
        'resistor': {'ohms': 10000, 'bands': ['brown', 'black', 'orange', 'gold'],
                     'placement': 'Between DATA and 3V3 if the module has no built-in pull-up.'}},
    'ds18b20': {
        'name': 'DS18B20', 'category': 'Sensors',
        'description': 'Digital one-wire temperature probe.',
        'roles': [('DATA', 'gpio'), ('VCC', 'power'), ('GND', 'ground')],
        'wiring': 'DATA → GPIO; VCC → 3V3; GND → GND; pull-up between DATA and 3V3.',
        'resistor': {'ohms': 4700, 'bands': ['yellow', 'violet', 'red', 'gold'],
                     'placement': 'Between DATA and 3V3.'}},
    'sht30': {
        'name': 'SHT30 / SHT31', 'category': 'Sensors',
        'description': 'I²C air temperature and relative humidity.',
        'roles': [('SDA', 'sda'), ('SCL', 'scl'), ('VCC', 'power'), ('GND', 'ground')],
        'wiring': 'SDA → even GP; SCL → next GP; VCC → 3V3; GND → GND. A bare I²C board needs pull-ups on both lines.',
        'resistor': {'ohms': 4700, 'bands': ['yellow', 'violet', 'red', 'gold'],
                     'placement': 'One from SDA to 3V3 and one from SCL to 3V3 if the breakout lacks pull-ups.'}},
    'tmp102': {
        'name': 'TMP102', 'category': 'Sensors',
        'description': 'I²C temperature sensor.',
        'roles': [('SDA', 'sda'), ('SCL', 'scl'), ('VCC', 'power'), ('GND', 'ground')],
        'wiring': 'SDA → even GP; SCL → next GP; VCC → 3V3; GND → GND. A bare I²C board needs pull-ups on both lines.',
        'resistor': {'ohms': 4700, 'bands': ['yellow', 'violet', 'red', 'gold'],
                     'placement': 'One from SDA to 3V3 and one from SCL to 3V3 if the breakout lacks pull-ups.'}},
    'tca9548a': {
        'name': 'TCA9548A I²C multiplexer', 'category': 'Multiplexers',
        'description': 'Adds eight selectable I²C channels for sensors that share an address.',
        'roles': [('SDA', 'sda'), ('SCL', 'scl'), ('VCC', 'power'), ('GND', 'ground')],
        'wiring': 'Upstream SDA/SCL connect to the Pico I²C pair. VCC → 3V3; GND → GND. Connect downstream devices to SD0/SC0 through SD7/SC7. Set A0–A2 for address 112–119.',
        'resistor': {'ohms': 4700, 'bands': ['yellow', 'violet', 'red', 'gold'],
                     'placement': 'Pull SDA and SCL to 3V3 only if the board lacks pull-ups. Check downstream boards too.'}},
}

instances = {}
shared_buses = {}
last_read = {}


def gpio_of(device, role):
    return HEADER_TO_GPIO[int(device['pins'][role])]


def address_of(device):
    default = {'sht30': 68, 'tca9548a': 112}.get(device['type'], 72)
    return int(device.get('address', default))


def validate(device, others, legacy_pins):
    if not isinstance(device, dict) or device.get('type') not in CATALOG:
        raise ValueError('Choose a supported device type')
    kind = device['type']
    if not isinstance(device.get('pins'), dict):
        raise ValueError('Choose every connection')
    if not 1 <= len(str(device.get('name', ''))) <= 60:
        raise ValueError('Name must be 1–60 characters')
    if len(str(device.get('note', ''))) > 120:
        raise ValueError('Note is too long')
    roles = CATALOG[kind]['roles']
    pins = device['pins']
    if set(pins) != set(role for role, _ in roles):
        raise ValueError('Choose every required connection')
    used_gpio = []
    for role, capability in roles:
        try:
            header = int(pins[role])
        except (TypeError, ValueError):
            raise ValueError('Invalid pin for ' + role)
        if capability == 'power' and header != POWER:
            raise ValueError('VCC must use physical pin 36 (3V3)')
        if capability == 'ground' and header not in GROUNDS:
            raise ValueError('GND must use a ground pin')
        if capability in ('gpio', 'adc', 'sda', 'scl'):
            gpio = HEADER_TO_GPIO.get(header)
            if gpio is None:
                raise ValueError(role + ' needs an exposed GPIO')
            if capability == 'adc' and gpio not in (26, 27, 28):
                raise ValueError('Analog sensors need GP26, GP27, or GP28')
            if capability == 'sda' and gpio % 2:
                raise ValueError('I2C SDA needs an even GP')
            used_gpio.append(gpio)
    if 'SDA' in pins:
        sda = gpio_of(device, 'SDA')
        if gpio_of(device, 'SCL') != sda + 1:
            raise ValueError('SCL must be the GP immediately after SDA')
        if not 0 <= address_of(device) <= 127:
            raise ValueError('Invalid I2C address')
        if kind == 'sht30' and address_of(device) not in (68, 69):
            raise ValueError('SHT30 address must be 68 or 69')
        if kind == 'tmp102' and address_of(device) not in (72, 73, 74, 75):
            raise ValueError('TMP102 address must be 72–75')
        if kind == 'tca9548a' and not 112 <= address_of(device) <= 119:
            raise ValueError('TCA9548A address must be 112–119')
    if kind == 'tca9548a':
        channels = device.get('channels')
        if not isinstance(channels, list) or len(channels) != 8:
            raise ValueError('Configure all eight multiplexer channels')
        for channel in channels:
            if not isinstance(channel, dict) or len(str(channel.get('name', ''))) > 40 or len(str(channel.get('note', ''))) > 120:
                raise ValueError('Invalid multiplexer channel')
    if len(set(used_gpio)) != len(used_gpio):
        raise ValueError('Each signal role needs a different GPIO')
    for gpio in used_gpio:
        if legacy_pins.get(str(gpio), {}).get('mode', 'unused') != 'unused':
            raise ValueError('GP%d already has manual configuration' % gpio)
    for other in others:
        if other.get('id') == device.get('id'):
            continue
        if 'SDA' in pins and 'SDA' in other['pins']:
            other_sda = gpio_of(other, 'SDA')
            this_sda = gpio_of(device, 'SDA')
            if other_sda != this_sda and (other_sda // 2) % 2 == (this_sda // 2) % 2:
                raise ValueError('I2C controller already uses another pin pair')
        for role, capability in CATALOG[other['type']]['roles']:
            if capability not in ('gpio', 'adc', 'sda', 'scl'):
                continue
            other_gpio = gpio_of(other, role)
            if other_gpio not in used_gpio:
                continue
            shared_i2c = capability in ('sda', 'scl') and kind in ('sht30', 'tmp102', 'tca9548a') and 'SDA' in other['pins'] and 'SDA' in pins
            if not shared_i2c:
                raise ValueError('GP%d is already used by %s' % (other_gpio, other['name']))
            if gpio_of(other, 'SDA') != gpio_of(device, 'SDA'):
                raise ValueError('I2C pin pair conflict')
            if address_of(other) == address_of(device):
                raise ValueError('I2C address already used on this bus')
    return True


def setup(all_devices):
    instances.clear()
    shared_buses.clear()
    last_read.clear()
    for device in all_devices:
        kind = device['type']
        ident = device['id']
        try:
            if kind in ('button', 'pir'):
                mode = machine.Pin.PULL_UP if kind == 'button' else None
                instances[ident] = machine.Pin(gpio_of(device, 'SIGNAL'), machine.Pin.IN, mode)
            elif kind in ('led', 'active_buzzer', 'relay_module'):
                instances[ident] = machine.Pin(gpio_of(device, 'SIGNAL'), machine.Pin.OUT, value=0)
            elif kind == 'soil_moisture':
                instances[ident] = machine.ADC(gpio_of(device, 'ANALOG'))
            elif kind == 'dht22':
                import dht
                instances[ident] = dht.DHT22(machine.Pin(gpio_of(device, 'DATA')))
            elif kind == 'ds18b20':
                import ds18x20
                import onewire
                instances[ident] = ds18x20.DS18X20(onewire.OneWire(machine.Pin(gpio_of(device, 'DATA'))))
            elif kind in ('sht30', 'tmp102', 'tca9548a'):
                sda = gpio_of(device, 'SDA')
                if sda not in shared_buses:
                    shared_buses[sda] = machine.I2C((sda // 2) % 2,
                        sda=machine.Pin(sda), scl=machine.Pin(sda + 1), freq=100000)
                instances[ident] = shared_buses[sda]
        except Exception as exc:
            print('Device', ident, 'setup error:', exc)


def crc8(data):
    crc = 255
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 255 if crc & 128 else (crc << 1) & 255
    return crc


def reading(device):
    ident = device['id']
    kind = device['type']
    current = time.ticks_ms()
    ttl = 2000 if kind == 'dht22' else 1000 if kind in ('ds18b20', 'sht30', 'tmp102') else 0
    cached = last_read.get(ident)
    if cached and time.ticks_diff(current, cached[0]) < ttl:
        return cached[1]
    try:
        sensor = instances[ident]
        if kind == 'button':
            result = {'pressed': sensor.value() == 0}
        elif kind in ('pir', 'led', 'active_buzzer', 'relay_module'):
            result = {'value': sensor.value()}
        elif kind == 'soil_moisture':
            raw = sensor.read_u16()
            result = {'raw_u16': raw, 'volts': round(raw * 3.3 / 65535, 4)}
        elif kind == 'dht22':
            sensor.measure()
            result = {'temperature_c': sensor.temperature(), 'humidity_percent': sensor.humidity()}
        elif kind == 'ds18b20':
            roms = sensor.scan()
            if not roms:
                raise ValueError('No DS18B20 found')
            sensor.convert_temp()
            time.sleep_ms(750)
            result = {'temperature_c': sensor.read_temp(roms[0])}
        elif kind == 'sht30':
            addr = address_of(device)
            sensor.writeto(addr, b'\x24\x00')
            time.sleep_ms(20)
            raw = sensor.readfrom(addr, 6)
            if crc8(raw[:2]) != raw[2] or crc8(raw[3:5]) != raw[5]:
                raise ValueError('SHT30 CRC check failed')
            result = {'temperature_c': round(-45 + 175 * ((raw[0] << 8) | raw[1]) / 65535, 2),
                      'humidity_percent': round(100 * ((raw[3] << 8) | raw[4]) / 65535, 2)}
        elif kind == 'tmp102':
            raw = sensor.readfrom_mem(address_of(device), 0, 2)
            value = (raw[0] << 4) | (raw[1] >> 4)
            if value & 0x800:
                value -= 4096
            result = {'temperature_c': value * 0.0625}
        elif kind == 'tca9548a':
            result = {'channels': 8, 'address': address_of(device)}
        else:
            result = None
    except Exception as exc:
        result = {'error': str(exc)}
    last_read[ident] = (time.ticks_ms(), result)
    return result


def view(device):
    result = dict(device)
    result['reading'] = reading(device)
    return result
