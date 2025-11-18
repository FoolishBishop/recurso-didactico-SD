# pn532_i2c.py  —  PN532 I2C driver (MicroPython, Pico)
# - Lectura robusta con status-byte (0x00/0x01) al inicio de cada lectura
# - Re-sincronización buscando 00 00 FF en respuestas
# - Tolerante a postamble opcional y 0x00 "fantasma"
# - Auto-fallback de escritura: combinado (0x00+frame) → separado (wake, frame)
# - API: get_firmware_version(), SAM_configuration(), read_passive_target(), in_list_passive_target()
#
# Uso típico:
#   from machine import Pin, I2C
#   from pn532_i2c import PN532_I2C, PN532_I2C_ADDR
#   i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=100000)
#   pn = PN532_I2C(i2c, addr=0x24, debug=False)
#   print(pn.get_firmware_version())
#   pn.SAM_configuration()
#   uid = pn.read_passive_target(timeout_ms=1000)

from time import sleep_ms, ticks_ms, ticks_diff

PN532_I2C_ADDR = 0x24  # Dirección 7-bit
PREAMBLE   = 0x00
STARTCODE1 = 0x00
STARTCODE2 = 0xFF
POSTAMBLE  = 0x00

TFI_HOST  = 0xD4
TFI_PN532 = 0xD5

ACK_FRAME = bytes([0x00, 0x00, 0xFF, 0x00, 0xFF, 0x00])

CMD_GET_FIRMWARE         = 0x02
CMD_SAM_CONFIGURATION    = 0x14
CMD_INLISTPASSIVETARGET  = 0x4A  # 106 kbps tipo A si BrTy=0x00


class PN532_I2C:
    def __init__(self, i2c, addr=PN532_I2C_ADDR, timeout_ms=2500, debug=False, rst_pin=None):
        """
        i2c: instancia machine.I2C o SoftI2C
        addr: 0x24 normalmente
        timeout_ms: espera para ready/lecturas
        debug: imprime TX/RX
        rst_pin: opcional, objeto Pin con .value() para resetear el módulo
        """
        self.i2c = i2c
        self.addr = addr
        self.timeout_ms = timeout_ms
        self.debug = debug
        self.rst_pin = rst_pin
        self._use_split_writes = False  # auto-ajuste si falla la combinada
        self._wakeup()

    # ---------- Utilidades internas ----------

    def _hw_reset(self):
        if self.rst_pin is not None:
            try:
                self.rst_pin.value(0)
                sleep_ms(100)
                self.rst_pin.value(1)
                sleep_ms(10)
            except Exception:
                pass

    def _wakeup(self):
        # Intento de reset por pin si está disponible
        self._hw_reset()
        # Intento de “wake” por I2C (algunos módulos lo ignoran si ya están despiertos)
        try:
            self.i2c.writeto(self.addr, b'\x00')
        except OSError:
            pass
        sleep_ms(10)

    def _wait_ready(self, timeout_ms=None):
        if timeout_ms is None:
            timeout_ms = self.timeout_ms
        t0 = ticks_ms()
        while ticks_diff(ticks_ms(), t0) < timeout_ms:
            try:
                status = self.i2c.readfrom(self.addr, 1)[0]
            except OSError:
                status = 0
            if status == 0x01:  # listo
                return True
            sleep_ms(5)
        return False

    def _build_frame(self, data_bytes):
        # data_bytes incluye [TFI_HOST, CMD, ...params]
        length = len(data_bytes)
        lcs = (0x100 - length) & 0xFF
        dsum = sum(data_bytes) & 0xFF
        dcs = (0x100 - dsum) & 0xFF
        return bytes([
            PREAMBLE, STARTCODE1, STARTCODE2,
            length, lcs
        ]) + bytes(data_bytes) + bytes([dcs, POSTAMBLE])

    def _write_frame(self, data_bytes):
        """
        En PN532 I2C, comúnmente se escribe 0x00 + frame en una transacción.
        Algunos módulos requieren wake separado. Intentamos combinado y
        hacemos fallback automático a separado.
        """
        frame = self._build_frame(data_bytes)

        if not self._use_split_writes:
            # ---- Modo combinado: 0x00 + frame ----
            payload = b'\x00' + frame
            if self.debug:
                print("TX(combined):", payload)
            try:
                self.i2c.writeto(self.addr, payload)
                sleep_ms(3)
                return
            except OSError as e:
                if self.debug:
                    print("TX combined falló, cambiando a split:", e)
                self._use_split_writes = True

        # ---- Modo split: wake y luego frame ----
        if self.debug:
            print("TX(wake):", b'\x00')
            print("TX(frame):", frame)
        try:
            self.i2c.writeto(self.addr, b'\x00')
        except OSError:
            pass
        sleep_ms(5)
        try:
            self.i2c.writeto(self.addr, frame)
        except OSError:
            sleep_ms(5)
            try:
                self.i2c.writeto(self.addr, b'\x00')
            except OSError:
                pass
            sleep_ms(5)
            self.i2c.writeto(self.addr, frame)
        sleep_ms(5)

    def _read_n(self, n):
        """
        Lee exactamente n bytes útiles del PN532.
        El PN532 por I2C puede anteponer un status-byte (0x00/0x01) al INICIO DE CADA LECTURA.
        Acumula bytes hasta reunir n, descartando status líderes repetidos.
        """
        out = bytearray()
        for _ in range(40):
            if len(out) >= n:
                break
            to_read = (n - len(out)) + 2  # +2 por si vuelve a meter status
            chunk = self.i2c.readfrom(self.addr, to_read)
            if chunk and chunk[0] in (0x00, 0x01):
                chunk = chunk[1:]  # descartar status líder
            if chunk:
                need = n - len(out)
                out.extend(chunk[:need])
        if len(out) != n:
            raise RuntimeError("Lectura con longitud inesperada (got %d, want %d): %s"
                               % (len(out), n, bytes(out)))
        if self.debug:
            print("RX:", bytes(out))
        return bytes(out)

    def _read_ack(self):
        if not self._wait_ready():
            raise RuntimeError("PN532 no responde (ACK timeout)")
        ack = self._read_n(6)
        if ack != ACK_FRAME:
            raise RuntimeError("ACK inválido: %s" % ack)

    def _read_response(self, expected_cmd=None):
        """
        Lee una respuesta completa del PN532 con re-sincronización:
        - Busca 00 00 FF
        - Soporta long frames (FF FF LEN2 LCS2)
        - Acepta postamble opcional y 0x00 fantasma
        """
        if not self._wait_ready():
            raise RuntimeError("PN532 no responde (DATA timeout)")

        def checksum_ok(d, c):
            return (((sum(d) & 0xFF) + (c & 0xFF)) & 0xFF) == 0

        # 1) Leer un bloque generoso y ubicar startcode
        raw = self._read_n(100)
        sc = b"\x00\x00\xFF"
        start = raw.find(sc)
        if start < 0:
            # Un intento extra si justo cortó
            raw += self._read_n(40)
            start = raw.find(sc)
            if start < 0:
                raise RuntimeError("No se encontró startcode 00 00 FF en respuesta")

        # 2) Leer LEN/LCS (o extended)
        # Asegura tener al menos 5 bytes tras 'start'
        if start + 5 > len(raw):
            raw += self._read_n(start + 5 - len(raw))
        len1 = raw[start+3]
        lcs1 = raw[start+4]

        ext = (len1 == 0xFF and lcs1 == 0xFF)
        if ext:
            # Extended length: FF FF LEN2(2) LCS2(1)
            # Asegura tener 3 bytes más
            if start + 8 > len(raw):
                raw += self._read_n(start + 8 - len(raw))
            len2_hi = raw[start+5]
            len2_lo = raw[start+6]
            lcs2    = raw[start+7]
            length  = (len2_hi << 8) | len2_lo
            # LCS2 es complemento a 16 bits: (LEN2 + LCS2) & 0xFFFF == 0
            if ((length + ((lcs2 << 8) | 0x00)) & 0xFFFF) != 0 and ((length + lcs2) & 0xFF) != 0:
                # algunos firmwares usan LCS2 de 8 bits; si ambas fallan, error
                raise RuntimeError("LCS2 inválido")
            header_len = 8  # 00 00 FF FF FF LEN2(2) LCS2(1)
        else:
            # Normal length
            if ((len1 + lcs1) & 0xFF) != 0:
                raise RuntimeError("LCS inválido")
            length = len1
            header_len = 5  # 00 00 FF LEN LCS

        # 3) Leer cuerpo: DATA(length) + DCS + (POST opcional)
        # Reservamos 2 bytes (DCS + POST). Si POST falta, lo toleramos abajo.
        need = header_len + length + 2
        if start + need > len(raw):
            raw += self._read_n(start + need - len(raw))

        body = raw[start + header_len : start + header_len + length + 2]
        if len(body) < length + 2:
            # Un intento más si justo cortó
            body += self._read_n(length + 2 - len(body))
            if len(body) < length + 2:
                raise RuntimeError("Respuesta incompleta (body corto)")

        # DATA = [TFI, RESP, PAYLOAD...], luego DCS y POST (opcional)
        data = body[:length]
        dcs  = body[length]
        post = body[length+1] if len(body) >= length + 2 else 0x00

        # Validación 1: estándar (con postamble)
        valid_std = (post == 0x00) and checksum_ok(data, dcs)

        # Validación 2: sin postamble (tomar DCS como último byte válido)
        data2 = body[:length-1] if length >= 1 else b""
        dcs2  = body[length-1] if length >= 1 else 0
        valid_no_post = checksum_ok(data2, dcs2)

        # Validación 3: 0x00 fantasma delante
        valid_ghost = False
        if not (valid_std or valid_no_post) and len(data) >= 2 and data[0] == 0x00:
            d3 = data[1:]
            c3 = dcs
            v3a = checksum_ok(d3, c3)  # con postamble
            v3b = False
            if not v3a and len(d3) >= 1:
                d3b = d3[:-1]
                c3b = d3[-1]
                v3b = checksum_ok(d3b, c3b)
                if v3b:
                    d3, c3 = d3b, c3b
            if v3a or v3b:
                data, dcs = d3, c3
                valid_ghost = True

        if not (valid_std or valid_no_post or valid_ghost):
            raise RuntimeError("DCS/POST inválido")

        # 4) Verificación TFI
        if not data or data[0] != TFI_PN532:
            # Heurística: si aún hay 0x00 fantasma, salta
            if len(data) >= 2 and data[0] == 0x00 and data[1] == TFI_PN532:
                data = data[1:]
            else:
                raise RuntimeError("TFI inválido (no PN532->Host)")

        resp_code = data[1] if len(data) > 1 else None
        payload   = data[2:] if len(data) > 2 else b""

        if expected_cmd is not None and resp_code != (expected_cmd + 1):
            raise RuntimeError("Código de respuesta inesperado: 0x%02X" %
                               (resp_code if resp_code is not None else -1))

        if self.debug:
            print("RESP payload:", payload)
        return payload

    def _call(self, cmd, params=b''):
        """
        Envía un comando PN532 y devuelve el payload (sin TFI/RESP/DCS/POST).
        """
        # Enviar comando
        self._write_frame(bytes([TFI_HOST, cmd]) + params)
        # ACK
        self._read_ack()
        # DATA
        return self._read_response(expected_cmd=cmd)

    # ---------- API pública ----------

    def get_firmware_version(self):
        """
        Devuelve (IC, Ver, Rev, Support)
        Ejemplo típico: (0x32, 0x01, 0x06, 0x07)
        """
        data = self._call(CMD_GET_FIRMWARE)
        if len(data) < 4:
            raise RuntimeError("Respuesta corta en firmware")
        return tuple(data[:4])

    def SAM_configuration(self, mode=0x01, timeout_50ms=0x14, irq=0x01):
        """
        Configura SAM:
        - mode=0x01 (Normal)
        - timeout_50ms: múltiplos de 50 ms (0x14 => ~1 s)
        - irq=0x01 (usar IRQ; no imprescindible en este driver)
        """
        self._call(CMD_SAM_CONFIGURATION, bytes([mode, timeout_50ms, irq]))
        return True

    def in_list_passive_target(self, brty=0x00, max_targets=0x01):
        """
        Devuelve lista de targets:
        [{'tg': int, 'uid': bytes, 'atqa': int, 'sak': int}, ...] o [] si no hay.
        brty=0x00 -> 106 kbps Type A.
        """
        try:
            data = self._call(CMD_INLISTPASSIVETARGET, bytes([max_targets, brty]))
        except Exception:
            return []

        # data = [NbTg, (Tg, ATQA(2), SAK, NFCIDLen, NFCID...)*NbTg]
        if len(data) < 1 or data[0] == 0:
            return []
        ntg = data[0]
        ofs = 1
        out = []
        for _ in range(ntg):
            if ofs + 4 > len(data):
                break
            tg   = data[ofs]; ofs += 1
            atqa = (data[ofs] << 8) | data[ofs+1]; ofs += 2
            sak  = data[ofs]; ofs += 1
            if ofs >= len(data):
                break
            uid_len = data[ofs]; ofs += 1
            uid = bytes(data[ofs:ofs+uid_len]); ofs += uid_len
            out.append({"tg": tg, "uid": uid, "atqa": atqa, "sak": sak})
        return out

    def read_passive_target(self, timeout_ms=1000, baud=0x00, max_targets=1):
        """
        Intenta detectar un tag ISO14443A (Mifare) y devuelve su UID (bytes) o None.
        baud=0x00 → 106 kbps tipo A
        """
        t0 = ticks_ms()
        while ticks_diff(ticks_ms(), t0) < timeout_ms:
            try:
                tgs = self.in_list_passive_target(baud, max_targets)
                if tgs:
                    return tgs[0]["uid"]
            except Exception:
                pass
            sleep_ms(50)
        return None
