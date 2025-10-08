// ==========================
// Arduino UNO — pantalla UTFT + encoder + I2C esclavo
// Recibe desde Pico mensajes tipo "UID:F3C45515" y los muestra
// ==========================

#include <Wire.h>
#include <UTFT.h>
#include <SPI.h>
#include <RotaryEncoder.h>



// Dirección I2C del Arduino como esclavo
#define UNO_ADDR 9
#define RESP_SIZE 32

// --- Pantalla ILI9341 (ajusta los pines según tu shield)
UTFT myGLCD(ILI9341_16, 38, 39, 40, 41);
extern uint8_t BigFont[];

// --- Encoder
#define PIN_IN1 A2
#define PIN_IN2 A3
RotaryEncoder encoder(PIN_IN1, PIN_IN2, RotaryEncoder::LatchMode::TWO03);
volatile bool encoderChanged = false;
int newPos = 0;
// Pre-calculate limits and threshold for readability
const byte MAX_POS = 50;
const byte CHANGE_THRESHOLD = 3;
byte letra = 0;

// Flag for detecting changes in encoder direction
volatile bool directionChanged = false;



// Variables de pantalla
int currentIndex = 0;
String received_msg = "";
int variables[] = { 20, 40, 60, 80 };  // posiciones base

// --- Prototipos
void drawLines();
void drawArrow(int index);
void showText(String msg);

// ==========================
// SETUP
// ==========================
void setup() {
  Serial.begin(9600);

  // --- I2C
  Wire.begin(UNO_ADDR);
  Wire.onReceive(DataReceive);
  Wire.onRequest(DataRequest);

  // --- Encoder
  attachInterrupt(digitalPinToInterrupt(PIN_IN1), encoderChange, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_IN2), encoderChange, CHANGE);

  // --- Pantalla
  myGLCD.InitLCD();
  myGLCD.clrScr();
  myGLCD.setFont(BigFont);
  drawLines();

  Serial.println("Arduino UNO listo para recibir UID por I2C");
}

// ==========================
// LOOP
// ==========================
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
      letra += direccion;
      letra = (letra + 4) % 4;  // Limitamos letra entre 0 y 3
      pasosDesdeUltimoCambio = 0;
      Serial.print("POS LETRA: ");
      Serial.println(letra);
    }
    pos = newPos;
    Serial.println(pos);
    drawArrow(letra);
  }
}


// ==========================
// INTERRUPCIONES
// ==========================
void encoderChange() {
  encoderChanged = true;
}

// ==========================
// FUNCIONES I2C
// ==========================
void DataReceive(int numBytes) {
  char buffer[RESP_SIZE] = { 0 };
  int i = 0;
  while (Wire.available() && i < RESP_SIZE - 1) {
    buffer[i++] = Wire.read();
  }
  String msg = String(buffer);
  msg.trim();
  Serial.print("I2C Recibido: ");
  Serial.println(msg);

  if (msg.startsWith("UID:")) {
    received_msg = msg.substring(4);
    showLetter(letra, received_msg);
  }
}

void DataRequest() {
  Wire.write("OK\n");
}

// ==========================
// FUNCIONES DE PANTALLA
// ==========================
void drawLines() {
  myGLCD.clrScr();
  int screenWidth = myGLCD.getDisplayXSize();
  int screenHeight = myGLCD.getDisplayYSize();

  int lineLength = 50;
  int spaceX = 25;
  int startX = (screenWidth - (lineLength * 4 + spaceX * 3)) / 2;
  int startY = screenHeight / 2;

  for (int i = 0; i < 4; i++) {
    myGLCD.setColor(255, 255, 255);
    int x1 = startX + i * (lineLength + spaceX);
    int x2 = x1 + lineLength;
    myGLCD.drawLine(x1, startY, x2, startY);
  }
  drawArrow(currentIndex);
}

void drawArrow(int index) {
  myGLCD.setColor(0, 0, 0);
  myGLCD.fillRect(0, 125, 300, 140);  // limpia
  int x = 48 + 74 * index;
  int y = 110;
  myGLCD.setColor(255, 255, 255);
  myGLCD.drawLine(x, y + 20, x - 5, y + 25);
  myGLCD.drawLine(x, y + 20, x + 5, y + 25);
}

// Mostrar las letras en base a indice y letra
void showLetter(int index, String letter) {
  myGLCD.setColor(0, 0, 0);                                    // bloque negro
  myGLCD.fillRect(20 + 74 * index, 90, 70 + 74 * index, 119);  // Draw a filled rectangle


  myGLCD.setColor(255, 255, 255);  // Color blanco para la letra
  myGLCD.setFont(BigFont);
  myGLCD.print(String(letter), 40 + 74 * index, 100);
}



// este es mas showcase para ver que recibe
void showText(String msg) {
  myGLCD.setColor(0, 0, 0);
  myGLCD.fillRect(0, 60, 320, 100);
  myGLCD.setColor(255, 255, 255);
  myGLCD.print(msg, CENTER, 80);
}
