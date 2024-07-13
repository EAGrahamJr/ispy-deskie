import asyncio
import time

from adafruit_bme680 import Adafruit_BME680_I2C


class EnvData:
    def __init__(self, t, g, h):
        self.temperature = t
        self.gas = g
        self.humidity = h
        self.air_quality = 0
        self.pressure = 0


class Beamer:
    TEMP_OFFSET = -4  # based on calibration
    HUMIDITY_OFFSET = 10  # based on calibration
    HUMIDITY_BASELINE = 40.0
    HUMIDITY_WEIGHTING = 0.25

    def __init__(self, i2c, burn_in: int = 300):
        self.bme = Adafruit_BME680_I2C(i2c)

        # should be same config as kotlin
        # _BME680_SAMPLERATES = (0, 1, 2, 4, 8, 16)
        self.bme.humidity_oversample = 1
        self.bme.temperature_oversample = 2
        self.bme.pressure_oversample = 16
        self.bme.filter_size = 0
        self.bme.set_gas_heater(320, 150)

        self._burn_in_time = int(time.time()) + burn_in

    async def read_environment(self, data: EnvData):
        last_temp = 0
        gas_baseline = None
        burn_in_data = []

        while True:
            temp = self.bme.temperature + self.TEMP_OFFSET
            data.temperature = (temp * 1.8) + 32
            t = int(temp * 10)
            if t != last_temp:
                # print(f"temp change {temp} ")
                last_temp = t
            data.gas = self.bme.gas
            data.humidity = self.bme.humidity + self.HUMIDITY_OFFSET
            data.pressure = self.bme.pressure * 0.02953

            # "burn-in" and air-quality
            if gas_baseline is None:
                if int(time.time()) < self._burn_in_time:
                    burn_in_data.append(data.gas)
                else:
                    gas_baseline = sum(burn_in_data[-50:]) / 50.0
            else:
                data.air_quality = self.air_quality(
                    data.gas,
                    gas_baseline,
                    data.humidity,
                    self.HUMIDITY_BASELINE,
                    self.HUMIDITY_WEIGHTING,
                )

            # TODO MQTT publish stuff -- shouldn't be 1 per cycle because that's dumb

            await asyncio.sleep(1)

    @staticmethod
    def air_quality(
            gas_reading,
            gas_baseline,
            humidity_reading,
            humidity_baseline,
            humidity_weighting,
    ):

        gas_offset = gas_baseline - gas_reading
        humidity_offset = humidity_reading - humidity_baseline

        if humidity_offset > 0:
            humidity_score = (
                    (100 - humidity_baseline - humidity_offset)
                    / (100 - humidity_baseline)
                    * (humidity_weighting * 100)
            )
        else:
            humidity_score = (
                    (humidity_baseline + humidity_offset)
                    / humidity_baseline
                    * (humidity_weighting * 100)
            )

        if gas_offset > 0:
            gas_score = (gas_reading / gas_baseline) * (
                    100 - (humidity_weighting * 100)
            )
        else:
            gas_score = 100 - (humidity_weighting * 100)

        return humidity_score + gas_score
