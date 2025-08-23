import os

from radio import EnvData
from requestor import Requestor


class WeatherGov(Requestor):
    def __init__(self, env_data:EnvData):
        super().__init__(env_data)

        # pause in minutes between updates
        self._weather_pause = int(
            os.getenv("WEATHER_PAUSE", "15")
        )

        # weather station
        self._weather_station = os.getenv("WEATHER_STATION", "kbfi")
        self._weather_uri = (
                "https://api.weather.gov/stations/"
                + self._weather_station
                + "/observations/latest"
        )
        self._weather_rqst_headers = {
            "User-Agent": "(ispy-deskmate, txcrackers@gmail.com)",
            "Accept": "application/geo+json",
        }

    def __weather_parse(self, response):
        weather_data = response.json()
        props = weather_data["properties"]
        temp = props["temperature"]["value"]
        if temp is None:
            self.logger.warning("No temperature data")
        else:
            self.env_data.temperature = int(temp * 1.8) + 32
        humid = props["relativeHumidity"]["value"]
        if humid is None:
            self.logger.warning("No pressure data")
        else:
            self.env_data.humidity = humid

    async def get_weather(self):
        await self._run_request(
            self._weather_uri,
            f"weather for {self._weather_station}",
            self.__weather_parse,
            self._weather_pause,
            self._weather_rqst_headers,
        )
