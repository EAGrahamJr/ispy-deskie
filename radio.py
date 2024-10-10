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
        return (
            f"[{time.tm_hour:02d}:{time.tm_min:02d}] {record.levelname} - {record.msg}"
        )


_logger = logging.getLogger("RadioHead")


class RadioHead:

    def __init__(self, env):
        self.env = env
        self.pool = socketpool.SocketPool(wifi.radio)
        _logger.setLevel(logging.INFO)
        _logger.addHandler(LogHandler())

        # read ENV
        self._time_pause = int(
            os.getenv("NTP_PAUSE", "60")
        )  # pause in minutes between updates

        self._weather_pause = int(
            os.getenv("WEATHER_PAUSE", "15")
        )  # pause in minutes between
        # updates
        station_id = os.getenv("WEATHER_STATION", "kbfi")
        self._weather_uri = (
                "https://api.weather.gov/stations/" + station_id + "/observations?limit=1"
        )
        self._weather_rqst_headers = {
            "User-Agent": "(ispy-deskmate, txcrackers@gmail.com)",
            "Accept": "application/geo+json",
        }

    def _time_parse(self, time_data):
        tz_hour_offset = int(time_data["utc_offset"][0:3])
        tz_min_offset = int(time_data["utc_offset"][4:6])
        if tz_hour_offset < 0:
            tz_min_offset *= -1
        unixtime = int(time_data["unixtime"] + (tz_hour_offset * 60 * 60)) + (
                tz_min_offset * 60
        )

        # create time struct and set RTC with it
        rtc.RTC().datetime = time.localtime(unixtime)

    def _weather_parse(self, weather_data):
        props = weather_data["features"][0]["properties"]
        temp = props["temperature"]["value"]
        if temp is None:
            _logger.warning(f"No temperature data")
        else:
            self.env.temperature = int(temp * 1.8) + 32
        humid = props["relativeHumidity"]["value"]
        if humid is None:
            _logger.warning(f"No pressure data")
        else:
            self.env.humidity = humid

    async def run_time(self):
        await self.run_request(
            "http://worldtimeapi.org/api/ip", "Time", self._time_parse, self._time_pause
        )

    async def get_weather(self):
        await self.run_request(
            self._weather_uri,
            "Weather",
            self._weather_parse,
            self._weather_pause,
            self._weather_rqst_headers,
        )

    async def run_request(
            self, uri: str, what: str, parser, pause: int = 15, rqst_headers=None
    ):
        while True:
            if wifi.radio.connected:
                request = adafruit_requests.Session(
                    self.pool, ssl.create_default_context()
                )
                response = None

                try:
                    _logger.info(f"Getting {what}")
                    response = request.get(uri, headers=rqst_headers)
                    data = response.json()
                    parser(data)

                except Exception as e:
                    await self._boo_boo(f"Unable to get {what}", e)
                finally:
                    if response is not None:
                        response.close()
                await asyncio.sleep(pause * 60)
            # otherwise wait for a connection
            else:
                _logger.warning(f"{what} waiting on connection")
                await asyncio.sleep(15)

    async def connect_wifi(self):
        """
        (Re-)Connect to the network.
        """
        _logger.debug("Checking WiFi")
        while not wifi.radio.connected:
            try:
                _logger.info("Connecting to WiFi")
                wifi.radio.connect(
                    ssid=os.getenv("WIFI_SSID"), password=os.getenv("WIFI_PASSWORD")
                )
            except Exception as e:
                await self._boo_boo("Error connecting wifi", e)

            if not wifi.radio.connected:
                await asyncio.sleep(2)
            else:
                _logger.warning(
                    f"Connected to WiFi - IP address: {wifi.radio.ipv4_address}"
                )

    async def _boo_boo(self, msg: str, error: Exception):
        _logger.error(f"{msg} - {str(error)}")
        # _logger.exception(error)
