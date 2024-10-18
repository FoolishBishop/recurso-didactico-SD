/**
 * Pin layout used:
 * -------------------------------------
 *             MFRC522      Arduino
 *             Reader/PCD   Uno/101
 * Signal      Pin          Pin
 * -------------------------------------
 * RST/Reset   RST          9
 * SPI SS 1    SDA(SS)      ** custom, take a unused pin, only HIGH/LOW required **
 * SPI SS 2    SDA(SS)      ** custom, take a unused pin, only HIGH/LOW required **
 * SPI MOSI    MOSI         11 / ICSP-4
 * SPI MISO    MISO         12 / ICSP-1
 * SPI SCK     SCK          13 / ICSP-3
 *
 * More pin layouts for other boards can be found here: https://github.com/miguelbalboa/rfid#pin-layout
 *
 */

#include <SPI.h>
#include <MFRC522.h>

#include <U8g2lib.h>
#include <RotaryEncoder.h>

// RFID
#define RST_PIN 9   // Configurable, see typical pin layout above
#define SS_1_PIN 6  // Configurable, take a unused pin, only HIGH/LOW required, must be different to SS 2
#define NR_OF_READERS 1

// ROTATORY ENCODER
#define PIN_IN1 A2
#define PIN_IN2 A3

// Create instances
RotaryEncoder encoder(PIN_IN1, PIN_IN2, RotaryEncoder::LatchMode::TWO03);
U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2(U8G2_R0);
MFRC522 mfrc522(SS_1_PIN, RST_PIN);

// Pre-calculate limits and threshold for readability
const byte MAX_POS = 50;
const byte CHANGE_THRESHOLD = 5;
byte letra = 0;

// Flag for detecting changes in encoder direction
volatile bool directionChanged = false;

// Function to handle encoder state changes (interrupt-safe)
void encoderChange() {
  directionChanged = true;
}

/**
 * Initialize.
 */
void setup() {
  u8g2.begin();
  Serial.begin(9600);  // Initialize serial communications with the PC

  SPI.begin();                          // Init SPI bus
  mfrc522.PCD_Init(SS_1_PIN, RST_PIN);  // Init each MFRC522 card

  // Attach interrupt for efficient rotary encoder handling
  attachInterrupt(digitalPinToInterrupt(PIN_IN1), encoderChange, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_IN2), encoderChange, CHANGE);

  Serial.println("Arduino UNO listo");
  screen("Setup listo");
}

/**
 * Main loop.
 */
void loop() {
  static int pos = 0;
  static int pasosDesdeUltimoCambio = 0;
  static int direccion = 0;

  encoder.tick();
  int newPos = encoder.getPosition();

  // Si se supera el valor máximo, reiniciamos el contador
  if (abs(newPos) > MAX_POS) {
    encoder.setPosition(0);
    newPos = 0;
    pos = 0;  // Reiniciamos también pos
  }

  if (newPos != pos) {
    int deltaPos = newPos - pos;
    if (deltaPos != 0) {
      direccion = deltaPos / abs(deltaPos);
      pasosDesdeUltimoCambio++;
    }

    if (pasosDesdeUltimoCambio == CHANGE_THRESHOLD) {
      letra += direccion;
      letra = (letra + 4) % 4;  // Limitamos letra entre 0 y 3
      pasosDesdeUltimoCambio = 0;
      // envia al pipico
      Serial.println("TI" + String(letra));
    }
    pos = newPos;
  }

  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    // mensaje para pipico caso 2
    String temp_var = dump_byte_arrayToString(mfrc522.uid.uidByte, mfrc522.uid.size);
    Serial.println("TH" + temp_var);
    // usar pantalla
    screen(temp_var);

    // lo de abajo es para RFID, mejor no tocar
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
  }
}

String dump_byte_arrayToString(byte *buffer, byte bufferSize) {
  String hexString = "";
  for (byte i = 0; i < bufferSize; i++) {
    hexString += String(buffer[i], HEX);
  }
  return hexString;
}

void screen(String val) {
  u8g2.clearBuffer();                  // clear the internal memory
  u8g2.setFont(u8g2_font_helvB12_tf);  // choose a suitable font at https://github.com/olikraus/u8g2/wiki/fntlistall
  u8g2.drawStr(2, 29, val.c_str());    // write something to the internal memory
  u8g2.sendBuffer();                   // transfer internal memory to the display
  delay(100);
  u8g2.clearBuffer();  // clear the internal memory
}