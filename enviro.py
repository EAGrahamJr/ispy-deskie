import asyncio
import time, os, rtc
import wifi, ssl, socketpool
import adafruit_requests
import adafruit_logging as logging


class EnvData:
    def __init__(self, t, g, h):
        self.temperature = t
        self.gas = g
        self.humidity = h
        self.air_quality = 0
        self.pressure = 0


class RadioHead:
    _logger = logging.getLogger("RadioHead")

    def __init__(self):
        self.pool = socketpool.SocketPool(wifi.radio)
        self._logger.setLevel(logging.INFO)

    async def run_time(self):
        pause = int(os.getenv("NTP_PAUSE", "60"))  # pause in minutes between updates

        while True:
            # if connected do our thing
            if wifi.radio.connected:
                request = adafruit_requests.Session(self.pool, ssl.create_default_context())
                response = None

                try:
                    self._logger.info("Getting current time:")

                    response = request.get("http://worldtimeapi.org/api/ip")
                    time_data = response.json()
                    tz_hour_offset = int(time_data['utc_offset'][0:3])
                    tz_min_offset = int(time_data['utc_offset'][4:6])
                    if (tz_hour_offset < 0):
                        tz_min_offset *= -1
                    unixtime = int(time_data['unixtime'] + (tz_hour_offset * 60 * 60)) + (
                                tz_min_offset * 60)

                    rtc.RTC().datetime = time.localtime(
                        unixtime)  # create time struct and set RTC with it
                except Exception as e:
                    self._logger.exception(e)
                finally:
                    if response is not None:
                        response.close()
                await asyncio.sleep(pause * 60)
            # otherwise wait for a connection
            else:
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
                    data.temperature = (temp * 1.8) + 32
                    data.humidity = props["relativeHumidity"]["value"]

                except Exception as e:
                    self._logger.exception(e)
                finally:
                    if response is not None:
                        response.close()
                await asyncio.sleep(pause * 60)
            # otherwise wait for a connection
            else:
                await asyncio.sleep(15)

    async def connect_wifi(self):
        """
        (Re-)Connect to the network. Exposed for other radio users to check.
        """
        self._logger.debug("Checking WiFi")
        while not wifi.radio.connected:
            self._logger.info("Connecting to WiFi")
            wifi.radio.connect(ssid=os.getenv('WIFI_SSID'), password=os.getenv('WIFI_PASSWORD'))
            if not wifi.radio.connected:
                self._logger.warning("Attempting to re-connect")
                await asyncio.sleep(2)
            else:
                self._logger.info(f"Connected to WiFi - IP address: {wifi.radio.ipv4_address}")
