#include <Keyboard.h>
#include <Mouse.h>

const String CLICK = "CLICK";

const int pin8 = 8;
const int pin7 = 7;
String opcao;

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(1);

  Keyboard.begin();

  pinMode(pin8, OUTPUT);
  digitalWrite(pin8, LOW);

  pinMode(pin7, OUTPUT);
  digitalWrite(pin7, LOW);
}

void loop() {

  if (Serial.available() > 0) {

    opcao = Serial.readString();

    if (opcao == "999") {
      macroComplexSd();
    } else if (opcao == "888") {
      macroComplexHP();
    } else if (opcao == "1") {
      clicarBotaoEsquerdo();
    } else if (opcao == "2") {
      zoom();
    } else if (opcao == "3") {
      enter();
    } else if (opcao.indexOf("/") >= 0) {
      comandoBarra(opcao.substring(1, opcao.length()));
    } else if (opcao.indexOf("!") >= 0) {      
      texto(opcao.substring(1, opcao.length()));
    } 
  }
}

void texto(String texto) {
  delay(20);
  Keyboard.print(texto);
  delay(20);
}

void comandoBarra(String comando) {
  enter();
  delay(100);
  Keyboard.write(220);
  delay(100);
  Keyboard.print(comando);
  delay(100);
  enter();
}

void clicarBotaoEsquerdo() {
  digitalWrite(pin8, LOW);
  delay(50);
  digitalWrite(pin8, HIGH);
  delay(10);
}

void enter() {
  Keyboard.press(KEY_RETURN);
  delay(100);
  Keyboard.release(KEY_RETURN);
  delay(100);
}

void zoom() {
  Mouse.move(0, 0, -1);
  delay(100);
  Mouse.move(0, 0, -1);
  delay(100);
  Mouse.move(0, 0, -1);
  delay(100);
  Mouse.move(0, 0, -1);
  delay(100);
  Mouse.move(0, 0, -1);
  delay(100);
}

void macroComplexSd() {
  //156 = Q
  //162 = W
  /*
      Keyboard.press(156);
      delay(83);
      Keyboard.release(156);
      delay(32);//9

      Keyboard.press(162);
      delay(83);
      Keyboard.release(162);
      delay(30);
      */

  /*
      Keyboard.press(156);
      delay(55);
      Keyboard.release(156);
      delay(50);

      Keyboard.press(162);
      delay(55);
      Keyboard.release(162);
      delay(55);
*/

  Keyboard.press(156);
  delay(73);
  Keyboard.release(156);
  delay(24);

  Keyboard.press(162);
  delay(73);
  Keyboard.release(162);
  delay(24);
}

void macroComplexHP() {
  Keyboard.press(156);  //Q
  delay(73);
  Keyboard.release(156);
  delay(24);

  Keyboard.press(69);  //E
  delay(73);
  Keyboard.release(69);
  delay(24);
}