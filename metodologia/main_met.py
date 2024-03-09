import dbread_functions as dread
import readRFID as rfidread
import screen_show as ss

# ESTE ES CON SOLO UN RFID!!!!!!!!
# https://pimylifeup.com/raspberry-pi-rfid-rc522/
# https://youtu.be/fR5XhHYzUK0?si=nQBOyccd5YHMkyzt
# pins led:
# sda: pin 3
# scl: pin 5 
# vcc = 3.3 v

old_letter = None
while True:
    hexcode_code = rfidread.read_rfid()
    new_letter = dread.read_values_hexcode(hexcode_code)
    if old_letter != new_letter:
        ss.show_screen(new_letter)
        new_letter = old_letter

# preparan function con cada uno por separado
