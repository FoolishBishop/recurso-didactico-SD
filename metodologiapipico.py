from machine import Pin, UART
from time import sleep


""""
Al recibir mensajes del Arduino, reaccionara con estos dos tipos de mensajes:
    - Tipo 1: TI[index]
    - Tipo 2: TH[hex_value]
"""

# Transforma los mensajes decodeados y actualiza palabra interna o index/cursor


def process_hex_idx(raw_data: str, intern_w: str, index: int) -> int | str:
    # Caso 1
    if raw_data.startswith("TI"):
        try:
            index = int(raw_data[2:])
        except ValueError:
            print("### ERROR: Valor de indice no se pudo procesar como numero ###")
            index = 0
        # TODO: funcion para actualizar en pantalla
        return index, None

    # Caso 2
    global hex_db
    if raw_data.startswith("TH"):
        column_value = find_file(raw_data[2:], 0, hex_db)
        if column_value is None:
            print("### ERROR: No se encontro el hex_value en la base de datos ###")
        letra = column_value[1]
        return index, replace_str_index(intern_w, index, letra)


# Adquiere datos de Arduino UNO"
def obtener_datos_ard_uno() -> str:
    while True:
        if uart0.any():
            data = uart0.readline()
            decodeado = data.decode()
            print(decodeado)
            return decodeado
        sleep(0.5)


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


# Revisa en la base de datos de palabras si existe (para imagen)
def revisar_si_es_palabra(val_interna) -> bool:
    global words_db
    if find_file(val_interna, 0, words_db) != None:
        return True
    else:
        return False


""""
NO ESTA EN USO HASTA PROXIMA CONEXION DE ARDUINO MEGA!

# funcion que enviara la informacion al MEGA, si no hay imagen mandar None (?)
def send_to_MEGA(word, image) -> None:
    mensaje = f"{word},{image}"
    uart2.write(mensaje)
    print("data mandada a Arduino MEGA")
"""

# Constantes
# TODO: colocar los paths correctos mas adelante
hex_db = '/database.csv'
words_db = '/words.csv'


# TODO: modificar codigo para poder volver a casilla vacia (ver arduinos? o boton de reinicio?)
# TODO: revisar si posicion 1 tiene indice 0
def main():
    global words_db
    cursor = 0
    palabra_interna = "    "

    while True:
        # Recibe y actualiza
        data = obtener_datos_ard_uno()
        print(f"SS{data}")
        cursor, new_intern = process_hex_idx(data, palabra_interna, cursor)
        if new_intern != None:
            palabra_interna = new_intern

        # Para imagen
        # Actualmente no esta en uso
        """"
        if revisar_si_es_palabra(palabra_interna):
            imagen = find_file(palabra_interna, 0, words_db)
            send_to_MEGA(palabra_interna, imagen)
            print("## ENCVIADO A PANTALLA CON IMAGEN ##")
        else:
            send_to_MEGA(palabra_interna, None)
        """


if __name__ == "__main__":
    # Inicializacion de comunicacion cor Arduino UNO
    uart0 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

    # Led del Pi Pico
    led = Pin(25, Pin.OUT)

    # encender/apagar led
    led.toggle()

    print("pico listo")
    main()
