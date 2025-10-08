
## Dispositivo didáctico interactivo basado en Arduino y Raspberry Pi orientado al aprendizaje de la lectoescritura en estudiantes de nivel primario con Síndrome de Down


## Mapa de Pines
| **Placa**         | **Conexión**                | **Pinout**    |
| ----------------- | --------------------------- | ------------- |
| Raspberry Pi Pico | Arduino MEGA                 | Rx → GP17    |
|                   |                             | Tx → GP16    |
| Arduino MEGA       | Raspberry Pi Pico           | Rx → A5        |
|                   |                             | Tx → A4        |
|                   | Módulo PN532 NFC RFID           | GND → GND   |
|                   |                             | VCC → 5V  |
|                   |                             | TXD → A4 |
|                   |                             | RXD → A5 |
|                   |                             | IRQ → Pin 8     |
|                   |                             | RSTO → Pin 9   |
|                   | Codificador Rotativo KY-040 | CLK → Pin A2  |
|                   |                             | DT → Pin A3   |
|                   |                             | VCC → 5V      |
|                   |                             | GND → GND     |
|                   | Módulo de pantalla táctil TFT LCD a Color de 3,2 pulgadas   | DB0 - DB7 → D37 - D30     |
|                   |                             | DB8 - DB15 → D22 - D29     |
|                   |                             | LCD_RESET → D41    |
|                   |                             | LED_A → 5V     |
|                   |                             | CS → D40     |
|                   |                             | RD → 3.3V     |
|                   |                             | VCC → 5V     |
|                   |                             | GND → GND     |

## Authors

- [@Alyzzzzaaa](https://github.com/Alyzzzzaaa)

- [@FoolishBishop](https://github.com/FoolishBishop)



