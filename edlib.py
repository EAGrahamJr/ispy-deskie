import sys


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
    except RuntimeError:
        try:
            i2c = (
                board.STEMMA_I2C() # type: ignore
            )  # For using the built-in STEMMA QT connector on a microcontroller
            print("Using STEMMA")
        except RuntimeError:
            print("Unable to locate I2C interface - is anything connected?")
            sys.exit(1)
    return i2c

def bw_color(image, palette):
    import displayio

    def gamma_adjust(color, gamma=2.2):
        return int(pow(color / 255.0, gamma) * 255)

    corrected_palette = displayio.Palette(len(palette))
    for i, color in enumerate(palette):
        r, g, b = color
        r = gamma_adjust(r)
        g = gamma_adjust(g)
        b = gamma_adjust(b)
        corrected_palette[i] = (r, g, b)
    return image, corrected_palette
