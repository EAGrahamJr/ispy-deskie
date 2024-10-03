#!/usr/bin/env python3

import neopixel
import board

import edlib

import asyncio
from display import Screen
from enviro import EnvData, RadioHead

i2c = edlib.i2c()

screen = Screen(i2c)

pixels = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.25)

async def display_stuff(data: EnvData):
    while True:
        screen.temp_humidity(int(data.temperature),int(data.humidity))
        screen.pressure(data.pressure)
        screen.update()
        await asyncio.sleep(30)

async def main():
    rh = RadioHead()

    # create shared objects
    env = EnvData(0, 0, 0)

    # these just run on their own
    ignored1 = asyncio.create_task(rh.run_time())
    ignored2 = asyncio.create_task(rh.get_weather(env))
    ignored3 = asyncio.create_task(display_stuff(env))

    while True:
        await rh.connect_wifi()
        await asyncio.sleep(5)


asyncio.run(main())
screen.close()
