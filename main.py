#!/usr/bin/env python3

from datetime import datetime

import edlib

import asyncio
from display import Screen
from enviro import Beamer, EnvData
from inputs import Gesture, GestureData, GamePad, GamePadData, InputData

i2c = edlib.i2c()

screen = Screen(i2c)
pad = GamePad(i2c)
gesture = Gesture(i2c)
bme = Beamer(i2c)


async def display_stuff(data: EnvData):
    while True:
        current_time = datetime.now()
        screen.tl(current_time.strftime("%H:%M"))
        screen.tr(f"{int(data.temperature)} @ {int(data.humidity)}")
        screen.br(f"{data.pressure:.2f} in.")
        if data.air_quality > 0.0:
            screen.bl(f"AQ: {data.air_quality:.1f}")
        else:
            screen.bl(f"G: {data.gas / 1000:.1f}")
        screen.update()
        await asyncio.sleep(0.5)


async def main():
    # create shared objects
    env = EnvData(0, 0, 0)
    wave = GestureData(0)
    gamepad = GamePadData(0, 0, 0, 0, 0, 0)
    data = InputData(gamepad, wave)

    # these just run on their own
    ignored1 = asyncio.create_task(bme.read_environment(env))
    ignored2 = asyncio.create_task(display_stuff(env))

    gesture_read = gesture.read_gesture(data)
    pad_read = pad.read_until(data)

    gesture_task = asyncio.create_task(gesture_read)
    pad_task = asyncio.create_task(pad_read)

    await asyncio.gather(gesture_task, pad_task)


asyncio.run(main())
screen.close()
