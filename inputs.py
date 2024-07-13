import asyncio
from datetime import datetime

import adafruit_logging as logging
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_seesaw.seesaw import Seesaw
from micropython import const


class GamePadData:
    def __init__(self, x, y, a, b, x_axis, y_axis):
        self.x = x
        self.y = y
        self.a = a
        self.b = b
        self.x_axis = x_axis
        self.y_axis = y_axis


class GestureData:
    def __init__(self, what):
        self.gesture = what


class InputData:
    def __init__(self, gamepad, gesture, running=True):
        self.gamepad = gamepad
        self.gesture = gesture
        self.running = running


class GamePad:
    BUTTON_X: int = const(6)
    BUTTON_Y: int = const(2)
    BUTTON_A: int = const(5)
    BUTTON_B: int = const(1)
    BUTTON_SELECT: int = const(0)
    BUTTON_START: int = const(16)
    button_mask = const(
        (1 << BUTTON_X)
        | (1 << BUTTON_Y)
        | (1 << BUTTON_A)
        | (1 << BUTTON_B)
        | (1 << BUTTON_SELECT)
        | (1 << BUTTON_START)
    )

    def __init__(self, i2c_bus):
        self._seesaw = Seesaw(i2c_bus, addr=0x50)
        self._seesaw.pin_mode_bulk(GamePad.button_mask, Seesaw.INPUT_PULLUP)

    async def read_until(self, input_data: InputData, stop_button: int = BUTTON_START):
        data = input_data.gamepad
        while input_data.running:
            data.x_axis = 1023 - self._seesaw.analog_read(14)
            data.y_axis = 1023 - self._seesaw.analog_read(15)

            buttons = self._seesaw.digital_read_bulk(GamePad.button_mask)

            data.x = not buttons & (1 << GamePad.BUTTON_X)
            data.y = not buttons & (1 << GamePad.BUTTON_Y)
            data.a = not buttons & (1 << GamePad.BUTTON_A)
            data.b = not buttons & (1 << GamePad.BUTTON_B)
            data.start = not buttons & (1 << GamePad.BUTTON_START)
            data.select = not buttons & (1 << GamePad.BUTTON_SELECT)

            if not buttons & (1 << stop_button):
                input_data.running = False

            await asyncio.sleep(0)


class Gesture:
    _logger = logging.getLogger("Gesture")

    def __init__(self, i2c_bus):
        self._apds = APDS9960(i2c_bus)
        self._apds.enable_proximity = True
        self._apds.enable_gesture = True
        self._apds.enable_color = True

        self._logger.setLevel(logging.INFO)

        # TODO set up MQTT device?

    async def read_gesture(self, input_data: InputData):
        data = input_data.gesture
        last_gesture = 0

        while input_data.running:
            gesture = self._apds.gesture()
            current_time = datetime.now()
            t = current_time.strftime("%H:%M")
            if gesture == 0x01:
                self._logger.info(f"{t} up")
            elif gesture == 0x02:
                self._logger.info(f"{t} down")
            elif gesture == 0x03:
                self._logger.info(f"{t} left")
            elif gesture == 0x04:
                self._logger.info(f"{t} right")
                if last_gesture == 0x01:
                    input_data.running = False
            if gesture != 0:
                data.gesture = gesture
                last_gesture = gesture

            await asyncio.sleep(0)
