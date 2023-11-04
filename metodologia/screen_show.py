import drivers
from time import sleep


def show_screen(letter):
    # ! /usr/bin/env python

    # Simple string program. Writes and updates strings.
    # Demo program for the I2C 16x2 Display from Ryanteck.uk
    # Created by Matthew Timmons-Brown for The Raspberry Pi Guy YouTube channel

    # Import necessary libraries for communication and display use

    # Load the driver and set it to "display"
    # If you use something from the driver library use the "display." prefix first
    display = drivers.Lcd()

    # Main body of code
    try:
        while True:
            # Remember that your sentences can only be 16 characters long!
            display.lcd_display_string(letter, 1)  # Write line of text to first line of display
    except KeyboardInterrupt:
        # If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
        display.lcd_clear()


def txt_show(val1, val2, val3, val4):
    # ...
    # este esp para poner lo que muestra _ _ _ _
    base = "_ _ _ _"
    if val1 is not None:
        base = base[:0] + val1 + base[0 + 1:]
    if val2 is not None:
        base = base[:2] + val2 + base[2 + 1:]
    if val3 is not None:
        base = base[:4] + val3 + base[4 + 1:]
    if val4 is not None:
        base = base[:6] + val4 + base[6 + 1:]
    return base
