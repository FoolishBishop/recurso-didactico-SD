from machine import Pin, UART
from time import sleep


uart0 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
uart1 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))


# el led del pi pico
led = Pin(25, Pin.OUT)

led.toggle()
print("pico listo")

# transforma el str que recive en una lista
def get_list_from_data(received_data: str):
    # [numero de lector, hex value]
    return received_data.split(",")


# para la variable interna
def replace_str_index(text: str, index: int, replacement: str) -> str:
    return f'{text[:index]}{replacement}{text[index+1:]}'


# busca en el csv
def find_file(value:str, column_position: int, file:str):
    # devuelve lista de la fila

    # database.csv: hex, letter
    # words.csv: word, image    <- TODO
    # ambos son posicion 0 en este contexto
    with open(file, 'r') as archivo:
        for fila, linea in enumerate(archivo):
            campos = linea.strip().split(',')
            if len(campos) > column_position and campos[column_position] == value:
                return campos
        return None


# actualiza para poder usar revisar_si_es_palabra(), para mandar imagenes, no es necesario para mandar al arduino MEGA
def actualizar_estado_palabra_interno(val_interna: str, received_data: str) -> str:
    transformed_data = get_list_from_data(received_data)
    letter_position = transformed_data[0]
    letter = find_file(transformed_data[0], 0)[1]
    interno_actualziado = replace_str_index(val_interna, letter_position, letter)
    return interno_actualziado


# revisa en la base de datos de palabras si esta ahi
def revisar_si_es_palabra(val_interna) -> bool:
    global words_db
    if find_file(val_interna, 0, words_db) != None:
        return True
    else:
        return False


# adquiere datos de uno de los dos sensores, viene como "n_de_lector,hex_value"
def obtener_datos() -> str:
    while True:
        if uart1.any():
            data1 = uart1.readline()
            decodeado1 = data1.decode()
            print(f"Lector 0: {decodeado1}")
            return decodeado1
        
        if uart0.any():
            data2 = uart0.readline()
            decodeado2 = data2.decode()
            print(f"Lector 1: {decodeado2}")
            return decodeado2
        sleep(0.5)


# funcion que enviara la informacion al MEGA, si no hay imagen mandar None (?)
def send_to_MEGA(word, image) -> None:
    mensaje = f"{word},{image}"
    uart2.write(mensaje)
    print("data mandada a Arduino MEGA")


# constantes

# TODO: colocar los paths correctos mas adelante
hex_db = '/database.csv'
words_db = '/words.csv'


# TODO: modificar codigo p/ poder volver a casilla vacia (ver arduinos? o boton de reinicio?)
def main():
    global words_db

    palabra_interna = "    "
    while True:
        data = obtener_datos()
        palabra_interna = actualizar_estado_palabra_interno(palabra_interna, received_data=data)
        if revisar_si_es_palabra(palabra_interna):
            imagen = find_file(palabra_interna, 0, words_db)
            send_to_MEGA(palabra_interna, imagen)
        else:
            send_to_MEGA(palabra_interna, None)
