// NOTAS

//*Event Handlers (COMUNICACION ARDUINO/PICO)
// Wire.onReceive(DataReceive); <-- para recibir data
// Wire.onRequest(DataRequest); <-- para mandar data0

// LIBRERIAS
//Libreria comunicacion I2C
#include <Wire.h>

// Libreria encoder
#include <SPI.h>
#include <RotaryEncoder.h>

// Libreria RFID
#include <Adafruit_PN532.h>  // Library for the NFC/RFID module! !! Please load by Arduino IDE !!!
// https://funduinoshop.com/en/blog/arduino/the-pn532-nfc-rfid-module-near-field-communication
// SDA (TXD): A4  SCL (RXD): A5

// Libreria pantalla
#include <UTFT.h>  //http://www.rinkydinkelectronics.com/library.php?id=51
//#include <UTFT_Geometry.h>

// Variables comunicacion I2C
#define UNO_ADDR 9
#define RESP_SIZE 15
// Variable transferencia de datos
String data = "";

// Configuración de la pantalla ILI9341
// UTFT myGLCD(ILI9341_16, 38, 39, 40, 41);

extern uint8_t BigFont[];
// Variables de posición para la flecha
int variables[] = { 20, 40, 60, 80 };
int currentIndex = 0;  // Índice de la variable actual para la flecha

// RFID
unsigned long cardid;               // Variable for the read TAG ID
#define PN532_IRQ (2)               // Define the IRQ port
#define PN532_RESET (3)             // Define the Reset connector
unsigned long startTime;            // Variable para almacenar el tiempo de inicio
uint8_t success;                    // Create variable
uint8_t uid[] = { 0, 0, 0, 0, 0 };  // Buffer to store the UID
uint8_t uidLength;                  // Length of the UID (4 or 7 bytes depending on ISO14443A card/chip type)

static unsigned long lastCardId = 0;
static int lastPos = -1;


Adafruit_PN532 nfc(PN532_IRQ, PN532_RESET);  // Create instance with I2C protocol

// ROTATORY ENCODER
#define PIN_IN1 A2  // CLK
#define PIN_IN2 A3  // DT

// Create instances
RotaryEncoder encoder(PIN_IN1, PIN_IN2, RotaryEncoder::LatchMode::TWO03);

// Pre-calculate limits and threshold for readability
const byte MAX_POS = 25;
const byte CHANGE_THRESHOLD = 3;
byte letra_pos = 0;

// Flag for detecting changes in encoder direction
volatile bool directionChanged = false;


void setup() {
  Serial.begin(9600);
  Serial.println("Iniciando programa...");

  // I2C
  Wire.begin(UNO_ADDR);
  Serial.println("Comunicacion I2C lista");


  // RFID
  nfc.begin();
  unsigned long versiondata = nfc.getFirmwareVersion();  // Read version number of firmware
  if (!versiondata) {                                    // If no response is received
    Serial.print("Can't find board !");                  // Send text "Can't find..." to serial monitor
    while (1)
      ;  // so long stop
  }
  Serial.println("Sensor RFID listo");

  // Attach interrupt for efficient rotary encoder handling
  attachInterrupt(digitalPinToInterrupt(PIN_IN1), encoderChange, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_IN2), encoderChange, CHANGE);
  Serial.println("Encoder listo");

  // Screen QUITAR DE COMENTARIOS DPS CUANDO ESTE EN EL MEGA !!!!!!!!
  // myGLCD.InitLCD();
  // myGLCD.clrScr();
  // drawLines();
  // Serial.println("Pantalla lista");

  Serial.println("Arduino UNO listo");
}

void loop() {
  // Encoder
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
      letra_pos += direccion;
      letra_pos = (letra_pos + 4) % 4;  // Limitamos letra entre 0 y 3
      pasosDesdeUltimoCambio = 0;
      Serial.println("Pos: " + String(letra_pos));
      // envia a pantalla !!!!!!!!!
      //drawArrow(letra_pos);
    }
    pos = newPos;
  }

  // RFID
  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 30);

  if (success) {
    if (uidLength == 4) {  // If the card/chip has 4 byte length....
      // Mifare Classic card
      cardid = uid[0];   //
      cardid <<= 8;      // Set the 4 byte blocks
      cardid |= uid[1];  //
      cardid <<= 8;      // to a single block
      cardid |= uid[2];  //
      cardid <<= 8;      // together
      cardid |= uid[3];  //

      if (cardid != lastCardId || letra_pos != lastPos) {
        lastCardId = cardid;
        lastPos = letra_pos;

        data = String(cardid) + "," + String(letra_pos);

        Wire.onRequest(DataRequest);  // envia el hex value de rfid a pico
        Wire.onReceive(DataReceive);  // pico devuelve el valor como letra
        // usar pantalla
        // showLetter(letra_pos, data);
      }
    }
  }
  success=0;
}

// !!! FUNCIONES !!!

// Funciones de comunicacion I2C
void DataReceive(int numBytes) {  // recibir data
  int i = 0;
  char recvData[RESP_SIZE];
  memset(recvData, 0, RESP_SIZE);
  while (Wire.available()) {
    recvData[i++] = Wire.read();
  }

  Serial.println("Recv Event: ");
  Serial.print(String(recvData));
}

void DataRequest() {              // mandar data
  String response = data + "\n";  // Agrega salto de línea al final
  Wire.write(response.c_str());   // Envía solo el contenido útil
  Serial.println("Sent resp: " + response);
}

// Funciones de pantalla

// void drawLines() {
//   myGLCD.clrScr();  // Limpia la pantalla

//   int screenWidth = myGLCD.getDisplayXSize();   // Ancho de la pantalla
//   int screenHeight = myGLCD.getDisplayYSize();  // Alto de la pantalla

//   int lineLength = 50;  // Longitud de las líneas
//   int spaceX = 25;      // Espaciado entre líneas

//   int startX = (screenWidth - (lineLength * 4 + spaceX * 3)) / 2;
//   int startY = screenHeight / 2;  // Centrar verticalmente

//   int colors[][3] = { { 255, 255, 255 }, { 255, 255, 255 }, { 255, 255, 255 }, { 255, 255, 255 } };  // Rojo, Verde, Azul, Amarillo

//   for (int i = 0; i < 4; i++) {
//     myGLCD.setColor(colors[i][0], colors[i][1], colors[i][2]);

//     int x1 = startX + i * (lineLength + spaceX);
//     int x2 = x1 + lineLength;
//     myGLCD.drawLine(x1, startY, x2, startY);

//     //myGLCD.setColor(255, 255, 255); // Blanco para el texto
//     //myGLCD.printNumI(variables[i], x1 + lineLength / 2 - 5, startY - 20);
//   }

//   // Dibujar la flecha centrada en la línea actual
//   //int arrowX = startX + currentIndex * (lineLength + spaceX) + lineLength / 2;
//   //drawArrow(arrowX, startY - 10);
// }

// void drawArrow(int index) {
//   //drawArrow(48+74*index, 110);
//   int x = 48 + 74 * index;
//   int y = 110;
//   myGLCD.setColor(0, 0, 0);           // bloque negro
//   myGLCD.fillRect(0, 125, 300, 140);  // Draw a filled rectangle

//   int arrowSize = 5;
//   myGLCD.setColor(255, 255, 255);  // Flecha blanca
//   myGLCD.drawLine(x, y + 20, x - arrowSize, y + arrowSize + 20);
//   myGLCD.drawLine(x, y + 20, x + arrowSize, y + arrowSize + 20);
// }

// void showLetter(int index, String letter) {
//   myGLCD.setColor(0, 0, 0);                                    // bloque negro
//   myGLCD.fillRect(20 + 74 * index, 90, 70 + 74 * index, 119);  // Draw a filled rectangle


//   myGLCD.setColor(255, 255, 255);  // Color blanco para la letra
//   myGLCD.setFont(BigFont);
//   myGLCD.print(String(letter), 40 + 74 * index, 100);
// }

// Funciones de encoder
// Function to handle encoder state changes (interrupt-safe)
void encoderChange() {
  directionChanged = true;
}
