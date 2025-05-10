import asyncio
import time
import os
import rtc

import wifi
import ssl
import socketpool
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

    def __init__(self, env: EnvData):
        self.env = env
        self.pool = socketpool.SocketPool(wifi.radio)
        _logger.setLevel(logging.INFO)
        _logger.addHandler(LogHandler())

        # read ENV
        # pause in minutes between updates
        self._time_pause = int(
            os.getenv("NTP_PAUSE", "60")
        )

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

    def __time_parse(self, response):
        data = response.json()
        # Set the local timezone to the one specified in the JSON.
        # Note: time.tzset() is available on Unix systems.
        os.environ['TZ'] = data["timeZone"]
        time.tzset()

        # Get the ISO 8601 datetime string.
        dt_str = data["dateTime"]  # e.g., "2025-05-10T11:39:21.5929708"

        # Split off the fractional seconds (if present) so we can process them separately.
        if '.' in dt_str:
            main_part, frac_part = dt_str.split('.')
            # Convert the fractional part into a fraction of a second.
            frac_seconds = float("0." + frac_part)
        else:
            main_part = dt_str
            frac_seconds = 0.0

        # Use time.strptime to parse the main part of the timestamp.
        # The format matches: YYYY-MM-DDTHH:MM:SS
        time_tuple = time.strptime(main_part, "%Y-%m-%dT%H:%M:%S")

        # Convert the local time tuple to seconds since the Epoch.
        # time.mktime() interprets the struct_time in the current local timezone.
        local_epoch = time.mktime(time_tuple)

        # Add the fractional seconds to capture the full precision.
        epoch_timestamp = local_epoch + frac_seconds

        # If you need an integer epoch value (truncating fractions), cast to int.
        epoch_seconds = int(epoch_timestamp)
        # create time struct and set RTC with it
        rtc.RTC().datetime = time.localtime(epoch_seconds)

    def __weather_parse(self, response):
        weather_data = response.json()
        props = weather_data["properties"]
        temp = props["temperature"]["value"]
        if temp is None:
            _logger.warning("No temperature data")
        else:
            self.env.temperature = int(temp * 1.8) + 32
        humid = props["relativeHumidity"]["value"]
        if humid is None:
            _logger.warning("No pressure data")
        else:
            self.env.humidity = humid

    async def run_time(self):
        await self.__run_request(
            "http://worldtimeapi.org/api/ip",
            "time",
            self.__time_parse,
            self._time_pause,
            rqst_headers={'accept':'application-json'}
        )

    async def get_weather(self):
        await self.__run_request(
            self._weather_uri,
            f"weather for {self._weather_station}",
            self.__weather_parse,
            self._weather_pause,
            self._weather_rqst_headers,
        )

    async def __run_request(
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
                    parser(response)

                except Exception as e:
                    await self.__boo_boo(f"Unable to get {what}", e)
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
                await self.__boo_boo("Error connecting wifi", e)

            if not wifi.radio.connected:
                await asyncio.sleep(2)
            else:
                _logger.warning(
                    f"Connected to WiFi - IP address: {wifi.radio.ipv4_address}"
                )

    async def __boo_boo(self, msg: str, error: Exception):
        _logger.error(f"{msg} - {str(error)}")
        # _logger.exception(error)
