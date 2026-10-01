# PicoPlantMonitor

## Printable Pico 2 W case

An [open case STL and dimensioned preview](hardware/pico2w_case/README.md) are included. The design leaves the USB end, pins, BOOTSEL button, and RUN pin accessible, aligns with the Pico's four mounting holes, and adds a wide side flange with four external M3 mounting holes.

MicroPython firmware for Raspberry Pi Pico 2 W. It hosts a mobile-friendly board view, a device catalog, a persistent pin editor, and JSON endpoints for readings and I²C operations. On first boot, the Pico creates the password-free Wi-Fi access point **PlantMontitor**. Connecting should trigger a captive-portal setup window on devices that support one. If it does not appear, open `http://192.168.4.1` in a browser. Save your LAN SSID and password. After reboot, open the Pico's DHCP address on your LAN. If the saved network is unavailable at boot, the setup AP returns after roughly 15 seconds. It also returns if an established connection drops.

The setup AP answers DNS requests with its own address and redirects HTTP connectivity checks to the setup page. Captive-portal pop-up behavior is controlled by the phone or computer OS; HTTPS requests cannot be redirected without a certificate warning. The captive redirect is active only while the setup AP is running.

The local site and JSON API require no authentication. Anyone on the same reachable network can change outputs, issue I²C writes, and change Wi-Fi settings, so use a trusted network. The open setup AP should only be used in a controlled location. Wi-Fi credentials reside in `config.json` on Pico flash; the file is excluded from version control.

## Install

1. Put the Pico 2 W into BOOTSEL mode. Flash the **RPI_PICO2_W** MicroPython UF2 from the [official board download](https://micropython.org/download/RPI_PICO2_W/).
2. Copy `boot.py`, `main.py`, `app.py`, `devices.py`, `auto_post.py`, `index.html`, `ui.js`, and `api-docs.js` to the MicroPython filesystem with `mpremote` or Thonny.
3. Reset the board. Join `PlantMontitor` and browse `http://192.168.4.1`.

`mpremote` example: `py -m mpremote connect auto fs cp boot.py main.py app.py devices.py auto_post.py index.html ui.js api-docs.js : + reset`

## Web interface

The **Board & devices** screen draws all 40 physical header pins in board order. Top View and Bottom View mirror the left and right pin banks while keeping USB at the top. Click a pin for its note, mode, and attached device roles. The top-view drawing includes a **Reset (web)** control between USB and the RP2350 chip; it restarts the firmware after confirmation. The physical button under USB is BOOTSEL, not reset. A separate hardware reset switch can be wired between RUN and GND. Add a supported device from the searchable catalog and assign its signal, power, and ground connections. Device-specific wiring and resistor color bands appear before saving. Device configuration is saved to Pico flash and applied after a reboot; notes save immediately. Configured outputs can be switched live. Device readings refresh every 10 seconds while the board screen is visible. **Refresh readings** updates all devices, while **Refresh now** on a sensor card forces a new measurement for that sensor, bypassing its short reading cache.

The TCA9548A I²C multiplexer entry lets you select the Pico's upstream SDA/SCL pins, power and ground, its 7-bit address (112–119), and a name/note for each of its eight downstream channel pairs. Click its device card to edit the wiring and channels. SHT30/SHT31 and TMP102 sensors can be assigned to a configured multiplexer channel, including multiple sensors with the same I²C address on different channels. Their device API readings select the channel automatically.

The **Apps** screen contains an I²C Explorer. It lists configured Pico buses and multiplexer channels, scans a selected path, and reads or writes 1–32 bytes at a decimal address. A register number is optional. Hex input such as `24 00` writes two bytes. Requests use the selected multiplexer channel and take effect immediately; consult the target device's datasheet before writing.

The **API** screen has searchable example requests and responses for Wi-Fi changes, pin and device configuration, buttons, LEDs, multiplexer sensors, and raw I²C operations. Each example includes a short wiring note; hardware examples show illustrated Pico, wire, component, and physical-pin connections. LED examples include a 330 Ω resistor and its color bands. I²C examples explain optional 4.7 kΩ pull-ups when boards lack them. Replace example IDs, network names, and readings with your own values.

The **Wifi** screen holds network setup. It shows the saved SSID, lets you enter a new network, and has an explicit open-network option. Leaving the password blank for the same SSID keeps the existing saved password; the password is never returned by the API.

Each **sensor** has an Auto post checkbox (off by default), a 1-minute, 1-hour, 13-hour, or 24-hour interval, and a destination URL. For example, an SHT30 with `temperature_c: 22.5` and `humidity_percent: 48.1` can use `https://example.com/reading?temperature_c={temperature_c}&humidity_percent={humidity_percent}`. The Pico sends an HTTP POST to `/reading?temperature_c=22.5&humidity_percent=48.1` with an empty body. Placeholders use the sensor reading field names, such as `{temperature_c}` and `{humidity_percent}`. The Pico URL-encodes substituted values. It checks schedules once a minute while connected to Wi-Fi. The first send is due one interval after boot; a reboot starts that interval again. A failed sensor reading skips the send, and a failed delivery is logged on the Pico serial console; neither is queued for retry. Temperature readings display Fahrenheit beside Celsius on the site; distance readings display inches beside centimeters or millimeters when such a sensor is available.

## JSON API

- `GET /api/status` — network state, SSID, current IP.
- `POST /api/reboot` — restart the Pico firmware without changing saved settings.
- `GET /api/pins` — every exposed GPIO.
- `GET /api/pins/4` — one current reading with GP and physical header number, note, configuration and unit.
- `PUT /api/pins/4` — JSON such as `{"mode":"button","pull":"up","note":"Seed bay 2"}`. Saves to flash and reboots to apply the pin mode.
- `PUT /api/pins/14/value` — `{"value":1}` or `{"value":0}` for a pin already configured as `output`. Changes the live state without reboot; the configured initial value applies again on reboot.
- `PUT /api/wifi` — JSON `{"ssid":"network","password":"secret"}`; saves and reboots.

For `PUT /api/wifi`, `{"ssid":"current-network","password":""}` keeps the saved password when the SSID is unchanged. Send `{"ssid":"open-network","open_network":true}` to clear the password explicitly.

Supported devices: push button, single LED, 3.3 V active buzzer module, 3.3 V relay module, 3.3 V PIR module, capacitive analog soil moisture sensor, DHT22/AM2302, DS18B20, SHT30/SHT31, TMP102, and TCA9548A I²C multiplexer. A multiplexer has configurable names and notes for its eight downstream SD/SC channel pairs. The firmware reads sensors using its GPIO, ADC, MicroPython DHT/OneWire drivers, or I²C. No sensor type is inferred from a wire. Sensors that are not physically attached show a read error rather than a fabricated value. GPIO is 3.3 V logic; do not connect 5 V to it. Resistor guidance depends on whether your breakout already has pull-ups or a series resistor.


Sensor cards show specific troubleshooting suggestions when a reading fails. For I²C `EIO`, check the displayed SDA/SCL physical pins, 3V3 and ground, then scan that bus in **Apps → I²C Explorer**. An empty scan means nothing answered; check the sensor address, connections and pull-ups before changing firmware settings. A bare I²C bus may need 4.7 kΩ pull-ups from SDA and SCL to 3V3, while many breakouts already have them. DHT22 timeouts suggest checking its DATA line and a 10 kΩ pull-up if the sensor is bare. DS18B20 requires a 4.7 kΩ DATA pull-up. CRC errors suggest checking wiring quality and cable length. These are diagnostic suggestions, not proof of a specific fault.

Device API:

- `GET /api/catalog` — supported types, descriptions, wiring roles and resistor guidance.
- `GET /api/header` — all 40 physical header pins and assigned device roles.
- `GET /api/devices` and `GET /api/devices/1` — device configuration and current reading.
- `POST /api/devices/1/refresh` — force a new reading for one sensor and return its device record. This bypasses the sensor reading cache without rebooting.
- `POST /api/devices`, `PUT /api/devices/1`, `DELETE /api/devices/1` — manage a device; saves and reboots.
- `PUT /api/devices/1/value` — `{"value":1}` or `{"value":0}` for LED, buzzer or relay module output. This changes the live state; reboot returns outputs to off.
- `PUT /api/pins/4/note` — `{"note":"Seed bay 2"}` to update a GP note without reboot.
- `GET /api/i2c/buses` — configured Pico I²C paths and multiplexer channels.
- `POST /api/i2c/scan` — `{"bus":"direct:4"}` or `{"bus":"mux:3:0"}`.
- `POST /api/i2c/read` — `{"bus":"mux:3:0","address":68,"register":0,"count":2}`; omit or set `register` to `null` for a raw read.
- `POST /api/i2c/write` — `{"bus":"mux:3:0","address":68,"register":0,"data":[36,0]}`; omit or set `register` to `null` for a raw write.

`direct:4` refers to an I²C bus using GP4/GP5. `mux:3:0` refers to channel 0 of configured device ID 3. Call `GET /api/i2c/buses` to discover valid paths. I²C read results include `data` as decimal bytes and `hex` as an uppercase string; scan results include decimal `addresses`. Failed hardware transfers return HTTP 400 with an `error` message.

To assign a sensor to a mux channel, include its upstream Pico SDA/SCL pins and a `bus` path in the device request. For example, after adding mux ID `6` on GP4/GP5, `POST /api/devices` with `{"type":"sht30","name":"Seed bay 1","note":"Air","pins":{"SDA":6,"SCL":7,"VCC":36,"GND":8},"bus":"mux:6:0","address":68}`. The sensor's SDA/SCL wires go to mux `SD0`/`SC0`; `SDA`/`SCL` in JSON identify the mux's upstream Pico bus. Read the assigned sensor with `GET /api/devices/<id>`. Remove its assigned sensors before deleting the multiplexer.

## Optional Tailscale access

The Pico firmware does not run Tailscale. `tailnet-proxy/` provides a separate Tailscale node named `PicoPlantMonitor` on a powered-on Windows host and forwards its port 80 to the Pico's LAN IP. The proxy has its own persistent Tailscale state; its first run requires tailnet enrollment. Reserve the Pico's DHCP address on your router so the proxy target stays valid. This proxy does not add site authentication; tailnet access controls determine which devices can reach it.

To build the proxy: from `tailnet-proxy/`, run `go mod tidy` then `go build -o tailnet-proxy.exe .`. Start it with `./tailnet-proxy.exe -backend http://<PICO_LAN_IP>`; on first run, follow the Tailscale enrollment URL printed in the console. Once enrolled, use `http://picoplantmonitor.<YOUR_TAILNET>.ts.net/` from devices allowed by your tailnet policy. On Windows, `./install-task.ps1 -Backend http://<PICO_LAN_IP>` registers the proxy to start when your user logs on. The host PC must be powered on and the Pico must remain reachable on its LAN IP.
