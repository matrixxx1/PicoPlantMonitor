"""Minimal MicroPython SSD1306 I2C driver for 128x64 OLED modules."""

import framebuf


class SSD1306_I2C(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, address=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.address = address
        self.pages = height // 8
        self.buffer = bytearray(self.pages * width)
        super().__init__(self.buffer, width, height, framebuf.MONO_VLSB)
        self._init_display()

    def _command(self, value):
        self.i2c.writeto(self.address, bytes((0x80, value)))

    def _init_display(self):
        for command in (0xAE, 0x20, 0x00, 0x40, 0xA1, 0xC8, 0xA8,
                        self.height - 1, 0xD3, 0x00, 0xDA, 0x12, 0xD5,
                        0x80, 0xD9, 0xF1, 0xDB, 0x30, 0x81, 0xCF, 0xA4,
                        0xA6, 0x8D, 0x14, 0xAF):
            self._command(command)
        self.fill(0)
        self.show()

    def show(self):
        for command in (0x21, 0, self.width - 1, 0x22, 0, self.pages - 1):
            self._command(command)
        self.i2c.writeto(self.address, b'\x40' + self.buffer)
