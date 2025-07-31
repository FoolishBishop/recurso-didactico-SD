# Codigo mas reciente

from machine import Pin, I2C
from time import sleep
import sys


def setup():
    # Correr al inicio
    if not devices:
        print("No se encontró ningún dispositivo I2C.")
        sys.exit()

# Funciones para envio y recibimiento de datos


def sendData(x):
    i2c.writeto(addr, x.encode('utf-8'))  # Siempre enviar en bytes


def receiveData():
    """"
    Al recibir mensajes del Arduino se recibiran de esta forma:
    ID_RAW,INDEX
    """

    data = i2c.readfrom(addr, MSG_SIZE)
    print("Respuesta bruta:", data)
    end_idx = data.find(b'\n')  # Buscar hasta el delimitador \n
    if end_idx != -1:
        clean = data[:end_idx].decode('utf-8').strip()
        print("Respuesta:", clean)
        return clean
    else:
        print("Algo salio mal. Respuesta sin delimitador:", data)
        return data

# Funciones para procesamiento de datos

# Reemplaza mediante index en una string, para palabra_interna


def replace_str_index(text: str, index: int, replacement: str) -> str:
    return f'{text[:index]}{replacement}{text[index+1:]}'


# Busca en el CSV, devuelve lista de la fila que tiene el valor que buscabamos
def find_file(value: str, column_position: int, file: str) -> list | None:
    # database.csv: hex, letter
    # words.csv: word, image    <- TODO
    # ambos son posicion 0 en este contexto
    with open(file, 'r') as archivo:
        for fila, linea in enumerate(archivo):
            campos = linea.strip().split(',')
            if len(campos) > column_position and campos[column_position] == value:
                return campos
        return None


# Codigo principal
def main():
    # Variables paths (corroborar que sean los correctos)
    hex_db = '/database.csv'
    # words_db = '/words.csv'

    # Varibales procesamiento de datos
    palabra_interna = "    "

    # Variables de comunicacion
    MSG_SIZE = 32
    i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=100000)
    devices = i2c.scan()
    addr = devices[0]
    print(f"Dispositivo I2C encontrado en dirección: {hex(addr)}")

    setup()
    while True:
        # Hacer para esperar hasta recibir nueva data
        received_data = receiveData()
        print(f"Data recibida: {received_data}")
        received_data = received_data.split(",")
        try:
            index = int(received_data[1])
            column_value = find_file(received_data[0], 0, hex_db)
            if column_value:
                # Si se detecta el valor RFID en la base de datos
                letra = column_value[1]
                palabra_interna = replace_str_index(
                    palabra_interna, index, letra)
                print(f"Palabra interna: {palabra_interna}")
                # ^ No manda indice porque por si solo se dara cuenta de donde colocar
                sendData(letra)
                # Mas adelante, agregar señal en el caso necesario cuando se asocia a una imagen, todo en este if

        except ValueError:
            print("error en procesamiento de indice")
            index = 0

        # TODO: funcion para actualizar en pantalla


main()
