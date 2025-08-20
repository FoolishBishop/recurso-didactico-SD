# Codigo mas reciente

from machine import Pin, I2C
from time import sleep
import sys


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
    
    print("Programa inciado")
    if not devices:
        print("No se encontró ningún dispositivo I2C.")
        sys.exit()
    print("Se detecto dispositivo I2C")
    addr = devices[0]
    n=0

    print("Bucle iniciado")
    while True:
        # Recibir mensaje
        """"
        Al recibir mensajes del Arduino se recibiran de esta forma:
        ID_RAW,INDEX
        """

        try:
            n+=1
            data = str(i2c.readfrom(addr, MSG_SIZE))
            print(type(data))
            print("Respuesta bruta:", data)
            print(f"{n}")
            end_idx = data.find(b'\xff')  # Buscar hasta el delimitador /xff
            print(f"end idx # {end_idx}")
            if end_idx != -1:
                print("if")
                # print(len(data)) # 32 btw
                received_data = data.decode('ascii', errors='ignore')
                print(len(received_data))
                print(received_data)
                print("if end")
            else:
                print("Algo salio mal. Respuesta sin delimitador:", data)
                received_data = None
                sleep(1)
                continue
            
        except Exception as e:
            # print(f"[I2C Error al recibir]: {e}")
            received_data = None
            sleep(1)
            continue

        print(f"Data recibida: {received_data}")

        # Procesamiento de mensaje
        if received_data != None:
            print("NO FUCKING WAY SI FUNCIONO")
            sleep(10)
            try:
                received_data = received_data.split(",")

                if len(received_data) < 2:
                    print("Formato de datos inválido. Esperado: ID,INDEX")
                    continue

                index = int(received_data[1])
                print(f"Index: {index}")
                column_value = find_file(received_data[0], 0, hex_db)
                if column_value:
                    # Si se detecta el valor RFID en la base de datos
                    letra = column_value[1]
                    palabra_interna = replace_str_index(
                        palabra_interna, index, letra)
                    print(f"Palabra interna: {palabra_interna}")
                    # ^ No manda indice porque por si solo se dara cuenta de donde colocar

                    # Enviar al Arduino la letra del UID
                    try:
                        i2c.writeto(addr, letra.encode('utf-8'))
                    except Exception as e:
                        print(f"[I2C Error al enviar]: {e}")
                    # Mas adelante, agregar señal en el caso necesario cuando se asocia a una imagen, todo en este if

            except ValueError:
                print("error en procesamiento de indice")
                index = 0
            except Exception as e:
                print(f"Error inesperado: {e}")

        sleep(0.1)  # Para que no explote

        # TODO: funcion para actualizar en pantalla
        # TODO: funcion para ver si se puede hacer lista o no las variables recibidas, si no se puede entonces ignorar epicamente


main()

