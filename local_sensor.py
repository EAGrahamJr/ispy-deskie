import adafruit_ahtx0
import asyncio, os
from radio import EnvData


class TempSensor:
    def __init__(self, i2c, env: EnvData):
        self.env = env
        self.sensor = adafruit_ahtx0.AHTx0(i2c)
        # pause in minutes between updates
        self._weather_pause = int(
            os.getenv("WEATHER_PAUSE", "1")
        )
        # temperature offset
        self._temp_offset = int(
            os.getenv("TEMPERATURE_OFFSET", "-4")
        )

    async def get_weather(self):
        while True:
            temp = self.sensor.temperature + self._temp_offset
            self.env.temperature = int(temp * 1.8) + 32
            self.env.humidity = self.sensor.relative_humidity
            await asyncio.sleep(self._weather_pause * 60)
