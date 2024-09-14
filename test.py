from machine import Pin, UART
from time import sleep

uart0 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
uart1 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))


# el led del pi pico
led = Pin(25, Pin.OUT)
led.toggle()
print("pico listo")

while True:
    if uart1.any():
        data1 = uart1.readline()
        decodeado1 = data1.decode()
        print(f"el valor es0 {decodeado1}")
    sleep(0.1)
    
    if uart0.any():
        data2 = uart0.readline()
        decodeado2 = data2.decode()
        print(f"el valor es1 {decodeado2}")
    sleep(0.5)
