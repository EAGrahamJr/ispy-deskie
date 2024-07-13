def i2c(debug=False):
    """
    Creates the apprppriate I2C device for the environment (or fails).

    :param debug: if True (default Fault), returns a "wrapper" device that prints crap to the console
    :return:the "appropriate" I2C device
    """
    import board

    try:
        i2c = board.I2C()  # uses board.SCL and board.SDA
        print("Using I2C")
    except:
        try:
            i2c = (
                board.STEMMA_I2C()
            )  # For using the built-in STEMMA QT connector on a microcontroller
            print("Using STEMMA")
        except:
            print("Unable to locate I2C interface - is anything connected?")
            exit(1)
    return i2c


class I2CProxy:
    def __init__(self, i2c):
        self._i2c = i2c

    def write_then_readinto(self, **kwargs):
        print(kwargs)
        self._i2c.write_then_readinto(kwargs)

    def write(self, **kwargs):
        print(kwargs)
        self._i2c.write(kwargs)

    def writeto(self, **kwargs):
        print(kwargs)
        self._i2c.writeto(kwargs)

    def try_lock(self):
        return self._i2c.try_lock()

    def unlock(self):
        self._i2c.unlock()
