from time import sleep
# import drivers
# drivers es una carpeta con lo complicado y tembo
# fuente: https://github.com/the-raspberry-pi-guy/lcd
# se cambio a otro coso asi que ahora es este:
import lcdfunctionm4 as lsd
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import csv


def read_rfid():
    reader = SimpleMFRC522()
    while True:
        try:
            card_id, _ = reader.read()
            # lee como int
            return card_id
        finally:
            GPIO.cleanup()


def find_file(hexcode):
    # devuelve lista de la fila

    with open("metodologia.csv", 'r') as file:
        csvreader = csv.reader(file)
        for row in csvreader:
            if row[0] == str(hexcode):
                return row


""""
def show_screen(row_hex):
    # ! /usr/bin/env python

    # Simple string program. Writes and updates strings.
    # Demo program for the I2C 16x2 Display from Ryanteck.uk
    # Created by Matthew Timmons-Brown for The Raspberry Pi Guy YouTube channel

    # Import necessary libraries for communication and display use

    # Load the driver and set it to "display"
    # If you use something from the driver library use the "display." prefix first
    display = drivers.Lcd()
    # Main body of code
    letter = row_hex[1]
    line1 = letter

    try:
        display.lcd_clear()
        # max 16 characters
        display.lcd_display_string(string=line1, line=1)  # Write line of text to first line of display
        # (max 2 lines)
        display.lcd_display_string(string="jerma985", line=2)
    except KeyboardInterrupt:
        display.lcd_clear()
"""""


def main():
    hexc_old = None
    while True:
        hexcode = read_rfid()
        if hexcode != hexc_old:
            print(hexcode)
            list_row = find_file(hexcode)
            print("mostrando en pantalla...")
            # show_screen(list_row) <-- (old)
            lsd.lcd_string(list_row, 2)
            hexc_old = hexcode

if __name__ == "__main__":
    lsd.lcd_init()
    lsd.lcd_byte(lsd.LCD_LINE_1, lsd.LCD_CMD)
    sleep(1)
    print("esta corriendo")
    lsd.lcd_string("tengo cancer", 2)

    try:
        main()
    except KeyboardInterrupt:
        lsd.GPIO.cleanup()
        print("Exiting gracefully.")
