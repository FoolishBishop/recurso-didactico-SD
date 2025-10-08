# pn532_to_arduino.py — Pico lee PN532 y envía UID al Arduino (0x09)
from machine import I2C, Pin
from time import sleep_ms, ticks_ms, ticks_diff
from pn532_i2c import PN532_I2C, PN532_I2C_ADDR

UNO_ADDR = 0x09 # Arduino esclavo (Wire.begin(9))

def send_to_arduino(i2c, text: str):
    """Envía texto al UNO limitando a <=31 bytes (buffer típico de Wire ~32B)."""
    payload = (text or "")[:31]
    try:
        i2c.writeto(UNO_ADDR, payload.encode())
    except OSError as e:
        print("I2C write falló:", e)

def read_uid_once(nfc, timeout_ms=1000):
    """
    Devuelve UID (bytes) o None. Funciona con in_list_passive_target() o read_passive_target().
    """
    if hasattr(nfc, "in_list_passive_target"):
        try:
            ts = nfc.in_list_passive_target(0x00, 0x02) # 106 kbps Type A
            if not ts:
                return None
            t0 = ts[0]
            if isinstance(t0, dict):
                return t0.get("uid", None)
                return t0 if isinstance(t0, (bytes, bytearray)) else None
        except Exception:
            return None

        if hasattr(nfc, "read_passive_target"):
            try:
                return nfc.read_passive_target(timeout_ms=timeout_ms)
            except Exception:
                return None

    raise RuntimeError("Driver PN532 sin in_list_passive_target ni read_passive_target")


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



def main():
    # Variables importantes:
    # Variables paths (corroborar que sean los correctos)
    hex_db = '/database.csv'
    # words_db = '/words.csv'

    
    # 1) I2C a 50 kHz para máxima estabilidad en clones; si todo ok, podés subir a 100_000
    i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=50_000)

    # 2) Instanciar driver con timeout generoso; activar debug=True si querés ver RX/RESP
    nfc = PN532_I2C(i2c, debug=False, timeout_ms=2500)

    # 3) Escaneo útil para confirmar PN532 (0x24) y Arduino (0x09)
    devs = i2c.scan()
    print("I2C scan:", [hex(d) for d in devs])
    if PN532_I2C_ADDR not in devs:
        print("⚠️ PN532 (0x24) no visible. Revisa jumpers I2C y GND común.")
    if UNO_ADDR not in devs:
        print("⚠️ Arduino (0x09) no visible. Revisa dirección/wiring.")

    # 4) Wake-up suave del PN532
    try:
        i2c.writeto(PN532_I2C_ADDR, bytes([0x00]))
        sleep_ms(10)
    except OSError:
        pass

    # 5) Init PN532 (si tu clon es mañoso, puede fallar una vez; seguimos igual)
    try:
        fw = nfc.get_firmware_version()
        print("PN532 FW:", fw)
    except Exception as e:
        print("GET_FIRMWARE falló (seguimos):", e)
    try:
        nfc.SAM_configuration()
        print("SAM OK")
    except Exception as e:
        print("SAM_configuration falló (seguimos):", e)

    # 6) Aviso al Arduino de que estamos listos
    send_to_arduino(i2c, "READY")
    print("Acerque una tarjeta (ISO14443A)...")

    # 7) Loop de lectura con debouncing
    last_uid = None
    last_seen = 0

    while True:
        try:
            uid = read_uid_once(nfc, timeout_ms=800)
            if uid:
                now = ticks_ms()
                if (last_uid != uid) or (ticks_diff(now, last_seen) > 1500):
                    uid_hex = bytes(uid).hex().upper()
                    print("UID:", uid_hex)
                    
                    column_value = find_file(uid_hex, 0, hex_db)
                    if column_value:
                        # Si se detecta el valor RFID en la base de datos
                        letra = column_value[1]
                        print(f"LETRA DE UID {uid_hex}: {letra}")
                    else:
                        letra = None
                    
                    send_to_arduino(i2c, "UID:" + letra)
                    last_uid, last_seen = uid, now
                    sleep_ms(60) # enfriar cuando hay tarjeta presente
                else:
                    sleep_ms(150) # menos CPU cuando no hay tarjeta
        except Exception as e:
            print("Lectura falló:", e)
            sleep_ms(120)

if __name__ == "__main__":
    main()

