#!/usr/bin/env python3

import neopixel
import board

import edlib

import asyncio
from display import Screen
from local_sensor import TempSensor
from radio import EnvData, RadioHead

i2c = edlib.i2c()

screen = Screen(i2c)

pixels = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.25)


async def display_stuff(data: EnvData):
    while True:
        screen.update(data)
        await asyncio.sleep(30)


async def main():
    # create shared objects
    env = EnvData(0, 0, 0)

    # fills it
    rh = RadioHead(env)
    local = TempSensor(i2c, env)

    # these just run on their own
    ignored1 = asyncio.create_task(rh.run_time())
    ignored2 = asyncio.create_task(local.get_weather())
    ignored3 = asyncio.create_task(display_stuff(env))

    while True:
        await rh.connect_wifi()
        await asyncio.sleep(5)


asyncio.run(main())
screen.close()
