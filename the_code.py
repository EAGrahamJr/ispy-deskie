import asyncio

import board
import neopixel

import edlib
from display import Screen
from local_sensor import TempSensor
from radio import EnvData, RadioHead

# from weathergov import WeatherGov

i2c = edlib.i2c()

screen = Screen(i2c)

pixels = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.25) # type: ignore


async def display_stuff(data: EnvData):
    while True:
        screen.update(data)
        await asyncio.sleep(30)


async def main():
    # create shared objects
    env = EnvData(0, 0, 0)

    # fills it
    rh = RadioHead(env)
    weather = TempSensor(i2c, env)
    # weather = WeatherGov(env)

    # these just run on their own
    asyncio.create_task(rh.run_time())
    asyncio.create_task(weather.get_weather())
    asyncio.create_task(display_stuff(env))

    while True:
        await rh.connect_wifi()
        await asyncio.sleep(5)


asyncio.run(main())
screen.close()
