import dbread_functions as dread
import readRFID as rfidread
import screen_show as ss

# ESTE ES CON SOLO UN RFID!!!!!!!!

old_letter = None
while True:
    hexcode_code = rfidread.read_rfid()
    new_letter = dread.read_values_hexcode(hexcode_code)
    if old_letter != new_letter:
        ss.show_screen(new_letter)
        new_letter = old_letter

# preparan function con cada uno por separado