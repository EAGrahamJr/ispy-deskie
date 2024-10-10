import displayio
import i2cdisplaybus
import math
import time

from adafruit_display_text.label import Label
from adafruit_displayio_sh1106 import SH1106
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.line import Line
from adafruit_bitmap_font import bitmap_font

displayio.release_displays()
_WHITE = 0xFFFFFF

FONT = bitmap_font.load_font("fonts/WS_Regular-14.pcf")


class Screen:
    _WIDTH = 128
    _HEIGHT = 64
    # _DEGF = "℉"
    _DEGF = "F"

    def __init__(self, i2c):
        display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
        self.display = SH1106(display_bus, height=self._HEIGHT, width=self._WIDTH)
        self.display.wake()

        # Make the display context
        root = displayio.Group()
        self.display.root_group = root

        # add the clock
        self._clock = Clock(24)
        root.append(self._clock.get_group())

        # display the temperature and humidity as text in thetop
        self.temperature = Label(FONT, text="100F", color=_WHITE, x=56, y=8)
        # self.temperature.position = (56, 0)
        root.append(self.temperature)

        self.humidity = Label(FONT, text="100%", color=_WHITE, x=56, y=24)
        # self.humidity.anchored_position = (56, 16)
        root.append(self.humidity)

        self._status_group = displayio.Group(y=56)

    def update(self, data):
        temp = int(data.temperature)
        humid = int(data.humidity)
        self.temperature.text = f"{temp:>3}F"
        self.humidity.text = f"{humid:>3}%"
        self._clock.update()

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

    def update(self):
        current_time = time.localtime()
        hour = current_time.tm_hour
        minute = current_time.tm_min

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
