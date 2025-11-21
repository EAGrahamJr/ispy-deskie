from random import random

import displayio
import i2cdisplaybus
import math
import time
import terminalio

from adafruit_display_text.label import Label
from adafruit_displayio_sh1106 import SH1106
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.line import Line
from adafruit_bitmap_font import bitmap_font

from logger import get_logger

displayio.release_displays()
_WHITE = 0xFFFFFF

REG_FONT = bitmap_font.load_font("fonts/WS_Regular-14.pcf")
EIGHT_FONT = terminalio.FONT


class Screen:
    _WIDTH = 128
    _HEIGHT = 64
    # _DEGF = "℉"
    _DEGF = "F"

    _FORTUNES = (
        "It is certain",
        "Reply hazy, try again",
        "Don’t count on it",
        "Ask again later",
        "My reply is no",
        "Without a doubt",
        "Better not tell you now",
        "My sources say no",
        "Yes definitely",
        "Cannot predict now",
        "Outlook not so good",
        "You may rely on it",
        "Concentrate and ask again",
        "Very doubtful",
        "As I see it, yes",
        "Most likely",
        "Outlook good",
        "Yes",
        "Signs point to yes",
    )

    def __init__(self, i2c):
        self._logger = get_logger(__name__)
        display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
        self.display = SH1106(display_bus, height=self._HEIGHT, width=self._WIDTH + 4)
        self.display.brightness = 0.2
        self._display_on = True
        self._last_fortune = -1

        # Make the display context
        actual_root = displayio.Group()
        self.display.root_group = actual_root
        self.display_group = displayio.Group(x=2)
        actual_root.append(self.display_group)

        # add the clock
        self._clock = Clock(24)
        self.display_group.append(self._clock.get_group())

        # display the temperature and humidity as text in thetop
        self.temperature = Label(REG_FONT, text="100F", color=_WHITE, x=56, y=8)
        # self.temperature.position = (56, 0)
        self.display_group.append(self.temperature)

        self.humidity = Label(REG_FONT, text="100%", color=_WHITE, x=56, y=24)
        # self.humidity.anchored_position = (56, 16)
        self.display_group.append(self.humidity)

        self.fortune = Label(EIGHT_FONT, text="W" * 40, color=_WHITE, y=56)
        self.display_group.append(self.fortune)

    def update(self, data):
        current_time = time.localtime()
        hour = current_time.tm_hour
        minute = current_time.tm_min

        # TODO https://github.com/adafruit/Adafruit_CircuitPython_DisplayIO_SH1106/issues/21
        if hour < 8 or hour > 20:
            # self.display.sleep()
            if self.display._is_awake:
                self._logger.info("Go to sleep")
                self.display.bus.send(0xAE, b"")  # 0xAE = display off, sleep mode
                self.display._is_awake = False
            return

        # self.display.wake()
        if not self.display._is_awake:
            self._logger.info("Wakey")
            self.display.bus.send(0xAF, b"")  # 0xAE = display off, sleep mode
            self.display._is_awake = True

        temp = int(data.temperature)
        humid = int(data.humidity)
        self.temperature.text = f"{temp:>3}F"
        self.humidity.text = f"{humid:>3}%"
        self._clock.update(hour, minute)

        # fortune!
        if self._last_fortune == -1 or minute % 5 == 0:
            f = self._last_fortune
            while f == self._last_fortune:
                f = random.randint(1, len(self._FORTUNES)) - 1
            self.fortune.text = self._FORTUNES[f]
            self._last_fortune = f

    def close(self):
        self.display.root_group = None
        self.display.sleep()


class Clock:
    def __init__(self, radius: int = 16, x: int = 0, y: int = 0):
        self.radius = radius
        self.center_x = radius + x
        self.center_y = radius + y

        self._tick = radius / 8
        self._hl = radius / 2
        self._ml = radius - 2 * self._tick
        # Create a group to hold clock elements
        clock_group = displayio.Group()

        # Draw the clock face (circle)

        clock_face = Circle(radius, radius, radius - 1, outline=_WHITE)
        clock_group.append(clock_face)

        # Draw tick marks (every 5 minutes)
        for minute in range(0, 60, 5):
            angle = (minute / 60) * 2 * 3.14159
            x1 = radius + int(self._ml * math.cos(angle))
            y1 = radius + int(self._ml * math.sin(angle))
            x2 = radius + int((radius - self._tick) * math.cos(angle))
            y2 = radius + int((radius - self._tick) * math.sin(angle))
            tick_mark = Line(x1, y1, x2, y2, color=_WHITE)
            clock_group.append(tick_mark)

        self._group = clock_group
        self._start_size = len(clock_group)

    def get_group(self):
        return self._group

    def update(self, hour, minute):
        group = self._group
        if len(group) > self._start_size:
            group.pop()
            group.pop()

        # Draw hour hand
        hour_angle = (hour % 12 + minute / 60) * 30
        hour_x = int(self._hl * math.cos(math.radians(hour_angle - 90)))
        hour_y = int(self._hl * math.sin(math.radians(hour_angle - 90)))
        hour_hand = Line(
            self.center_x,
            self.center_y,
            self.center_x + hour_x,
            self.center_y + hour_y,
            color=_WHITE,
        )
        group.append(hour_hand)

        # Draw minute hand
        minute_angle = minute * 6
        minute_x = int(self._ml * math.cos(math.radians(minute_angle - 90)))
        minute_y = int(self._ml * math.sin(math.radians(minute_angle - 90)))
        minute_hand = Line(
            self.center_x,
            self.center_y,
            self.center_x + minute_x,
            self.center_y + minute_y,
            color=_WHITE,
        )
        group.append(minute_hand)
