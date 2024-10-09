import asyncio
import time, os, rtc

import wifi, ssl, socketpool
import adafruit_requests
import adafruit_logging as logging
from adafruit_logging import LogRecord


class EnvData:
    def __init__(self, t, g, h):
        self.temperature = t
        self.gas = g
        self.humidity = h
        self.air_quality = 0
        self.pressure = 0


class LogHandler(logging.StreamHandler):
    def __init__(self) -> None:
        super().__init__()

    def format(self, record: LogRecord) -> str:
        time = rtc.RTC().datetime
        return f"[{time.tm_hour:02d}:{time.tm_min:02d}] {record.levelname} - {record.msg}"

class RadioHead:
    _logger = logging.getLogger("RadioHead")

    def __init__(self):
        self.pool = socketpool.SocketPool(wifi.radio)
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(LogHandler())

    async def run_time(self):
        pause = int(os.getenv("NTP_PAUSE", "60"))  # pause in minutes between updates

        while True:
            # if connected do our thing
            if wifi.radio.connected:
                request = adafruit_requests.Session(self.pool, ssl.create_default_context())
                response = None

                try:
                    self._logger.info("Getting current time")

                    response = request.get("http://worldtimeapi.org/api/ip")
                    time_data = response.json()
                    tz_hour_offset = int(time_data['utc_offset'][0:3])
                    tz_min_offset = int(time_data['utc_offset'][4:6])
                    if (tz_hour_offset < 0):
                        tz_min_offset *= -1
                    unixtime = int(time_data['unixtime'] + (tz_hour_offset * 60 * 60)) + (
                                tz_min_offset * 60)

                    # create time struct and set RTC with it
                    rtc.RTC().datetime = time.localtime(unixtime)
                except Exception as e:
                    await self._boo_boo("Unable to get or set time",e)
                finally:
                    if response is not None:
                        response.close()
                await asyncio.sleep(pause * 60)
            # otherwise wait for a connection
            else:
                self._logger.warning("Time waiting on connection")
                await asyncio.sleep(15)

    async def get_weather(self, data: EnvData):
        pause = int(os.getenv("WEATHER_PAUSE", "15"))  # pause in minutes between updates
        station_id = os.getenv("WEATHER_STATION", "kbfi")
        weather_uri = "https://api.weather.gov/stations/" + station_id + "/observations?limit=1"
        rqst_headers = {"User-Agent": "(ispy-deskmate, txcrackers@gmail.com)",
                        "Accept": "application/geo+json"}

        while True:
            if wifi.radio.connected:
                request = adafruit_requests.Session(self.pool, ssl.create_default_context())
                response = None

                try:
                    self._logger.info("Getting weather")

                    response = request.get(weather_uri, headers=rqst_headers)
                    weather_data = response.json()
                    props = weather_data["features"][0]["properties"]
                    temp = props["temperature"]["value"]
                    if temp is None:
                        self._logger.warning(f"No temperature data")
                        data.temperature = 1.0
                    else:
                        data.temperature = int(temp * 1.8) + 32
                    humid = props["relativeHumidity"]["value"]
                    if humid is None:
                        self._logger.warning(f"No pressure data")
                        data.humidity = 1.0
                    else:
                        data.humidity = humid

                except Exception as e:
                    await self._boo_boo(f"Unable to get weather for {station_id}",e)
                finally:
                    if response is not None:
                        response.close()
                await asyncio.sleep(pause * 60)
            # otherwise wait for a connection
            else:
                self._logger.warning("Weather waiting on connection")
                await asyncio.sleep(15)

    async def connect_wifi(self):
        """
        (Re-)Connect to the network.
        """
        self._logger.debug("Checking WiFi")
        while not wifi.radio.connected:
            try:
                self._logger.info("Connecting to WiFi")
                wifi.radio.connect(ssid=os.getenv('WIFI_SSID'), password=os.getenv('WIFI_PASSWORD'))
            except Exception as e:
                await self._boo_boo("Error connecting wifi",e)

            if not wifi.radio.connected:
                await asyncio.sleep(2)
            else:
                self._logger.warning(f"Connected to WiFi - IP address: {wifi.radio.ipv4_address}")

    async def _boo_boo(self, msg:str, error:Exception):
        self._logger.error(f"{msg} - {str(error)}")
        # self._logger.exception(error)
