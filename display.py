import displayio
import i2cdisplaybus

# TODO https://github.com/adafruit/Adafruit_CircuitPython_DisplayIO_SSD1306/issues/45
# from adafruit_display_text.bitmap_label import Label
import terminalio
from adafruit_display_text.label import Label
from adafruit_displayio_ssd1306 import SSD1306

displayio.release_displays()
_WHITE = 0xFFFFFF


class Screen:
    _WIDTH = 128
    _HEIGHT = 32

    def __init__(self, i2c):
        display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
        self.display = SSD1306(
            display_bus, height=self._HEIGHT, width=self._WIDTH, auto_refresh=False
        )
        self.display.wake()

        # Make the display context
        self.root_group = displayio.Group()
        self.display.root_group = self.root_group

        # divvy the screen up into two regions
        self.top_left = Label(terminalio.FONT, text=" " * 10, color=_WHITE)
        self.top_left.anchor_point = (0.0, 0.0)
        self.top_left.anchored_position = (0, 0)
        self.root_group.append(self.top_left)

        self.top_right = Label(terminalio.FONT, text=" " * 10, color=_WHITE)
        self.top_right.anchor_point = (0.0, 0.0)
        self.top_right.anchored_position = (self._WIDTH / 2, 0)
        self.root_group.append(self.top_right)

        self.bottom_left = Label(terminalio.FONT, text=" " * 10, color=_WHITE)
        self.bottom_left.anchor_point = (0.0, 0.0)
        self.bottom_left.anchored_position = (0, self._HEIGHT / 2)
        self.root_group.append(self.bottom_left)

        self.bottom_right = Label(terminalio.FONT, text=" " * 10, color=_WHITE)
        self.bottom_right.anchor_point = (0.0, 0.0)
        self.bottom_right.anchored_position = (self._WIDTH / 2, self._HEIGHT / 2)
        self.root_group.append(self.bottom_right)

    def update(self):
        self.display.refresh()
        pass

    def tl(self, text: str) -> None:
        # print(f"tl {text}")
        self.top_left.text = text

    def bl(self, text: str) -> None:
        # print(f"bl {text}")
        self.bottom_left.text = text

    def tr(self, text: str) -> None:
        # print(f"tr {text}")
        self.top_right.text = text

    def br(self, text: str) -> None:
        self.bottom_right.text = text

    def close(self):
        self.display.root_group = None
        self.display.sleep()
