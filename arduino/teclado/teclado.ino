/*
  teclado_hid.ino — Leonardo/Micro (ATmega32u4)
  Protocolo via Serial (115200), uma linha por comando (terminada em \n):
    TAP:<KEY>           -> pressiona e solta (ou trata texto especial começando com '/')
    DOWN:<KEY>          -> pressiona e mantém
    UP:<KEY>            -> solta
    TYPE:<texto livre>  -> digita texto literal (se começar com '/', trata como comando)
    COMBO:<K1>+<K2>+... -> pressiona todos e solta ao final (ex.: LCTRL+LSHIFT+S)

  Teclado SEM NUMPAD: números são da linha superior '0'..'9'.
*/

#include <Keyboard.h>

String line;

// =================== DEFINES FIXOS (A–Z e 0–9) ===================
// Letras
#define KEY_A 97
#define KEY_B 98
#define KEY_C 99
#define KEY_D 100
#define KEY_E 101
#define KEY_F 102
#define KEY_G 103
#define KEY_H 104
#define KEY_I 105
#define KEY_J 106
#define KEY_K 107
#define KEY_L 108
#define KEY_M 109
#define KEY_N 110
#define KEY_O 111
#define KEY_P 112
#define KEY_Q 113
#define KEY_R 114
#define KEY_S 115
#define KEY_T 116
#define KEY_U 117
#define KEY_V 118
#define KEY_W 119
#define KEY_X 120
#define KEY_Y 121
#define KEY_Z 122


// Números (linha superior)
#define KEY_0  234
#define KEY_1  225
#define KEY_2  226
#define KEY_3  227
#define KEY_4  228
#define KEY_5  229
#define KEY_6  230
#define KEY_7  231
#define KEY_8  232
#define KEY_9  233

// ===== NUMPAD (códigos diretos, estilo KEY_0..9) =====
#define KEY_NUM_SLASH   220 // '\334' Keypad /
#define KEY_NUM_STAR    221 // '\335' Keypad *
#define KEY_NUM_MINUS   222 // '\336' Keypad -
#define KEY_NUM_PLUS    223 // '\337' Keypad +
#define KEY_NUM_ENTER   224 // '\340' Keypad Enter
#define KEY_NUM_1       225 // '\341' Keypad 1 (End)
#define KEY_NUM_2       226 // '\342' Keypad 2 (Down)
#define KEY_NUM_3       227 // '\343' Keypad 3 (PgDn)
#define KEY_NUM_4       228 // '\344' Keypad 4 (Left)
#define KEY_NUM_5       229 // '\345' Keypad 5
#define KEY_NUM_6       230 // '\346' Keypad 6 (Right)
#define KEY_NUM_7       231 // '\347' Keypad 7 (Home)
#define KEY_NUM_8       232 // '\350' Keypad 8 (Up)
#define KEY_NUM_9       233 // '\351' Keypad 9 (PgUp)
#define KEY_NUM_0       234 // '\352' Keypad 0 (Insert)
#define KEY_NUM_DOT     235 // '\353' Keypad . (Delete)


// Barra "/" corrigida (evita virar ';' no jogo)
#define KEY_SLASH_FIX 220
// ================================================================

// ---------- helpers ----------
void pressRelease(uint8_t kc) {            // padrão (teclas não-numéricas)
  Keyboard.press(kc);
  delay(50);
  Keyboard.release(kc);
}

void pressReleaseAscii(char ascii, uint16_t downMs = 80, uint16_t gapMs = 200) {
  Keyboard.press((uint8_t)ascii);
  delay(downMs);
  Keyboard.release((uint8_t)ascii);
  delay(gapMs);
}

void typeText(const String &txt) {         // texto literal (chat)
  for (size_t i = 0; i < txt.length(); ++i) {
    Keyboard.write((uint8_t)txt[i]);
    delay(5);
  }
}

// Envia "/" pelo código 220 e depois o texto; opcionalmente ENTER no fim
void sendSlashCommand(const String &rest, bool sendEnter = true) {
  Keyboard.write(KEY_SLASH_FIX);  // barra correta para o jogo
  delay(30);
  typeText(rest);                 // digita o restante como veio
}

bool modifierFromToken(const String &tok, uint8_t &mod) {
  if (tok=="LCTRL") { mod = KEY_LEFT_CTRL;  return true; }
  if (tok=="LSHIFT"){ mod = KEY_LEFT_SHIFT; return true; }
  if (tok=="LALT")  { mod = KEY_LEFT_ALT;   return true; }
  if (tok=="LGUI")  { mod = KEY_LEFT_GUI;   return true; }
  if (tok=="RCTRL") { mod = KEY_RIGHT_CTRL; return true; }
  if (tok=="RSHIFT"){ mod = KEY_RIGHT_SHIFT;return true; }
  if (tok=="RALT")  { mod = KEY_RIGHT_ALT;  return true; }
  if (tok=="RGUI")  { mod = KEY_RIGHT_GUI;  return true; }
  return false;
}

// especiais diretos do Keyboard.h
bool specialFromToken(const String &tok, uint8_t &kc) {
  if (tok=="ENTER")         { kc = KEY_RETURN; return true; }
  if (tok=="ESC")           { kc = KEY_ESC; return true; }
  if (tok=="BACKSPACE")     { kc = KEY_BACKSPACE; return true; }
  if (tok=="TAB")           { kc = KEY_TAB; return true; }
  if (tok=="CAPSLOCK")      { kc = KEY_CAPS_LOCK; return true; }

  if (tok=="LEFT")          { kc = KEY_LEFT_ARROW; return true; }
  if (tok=="RIGHT")         { kc = KEY_RIGHT_ARROW; return true; }
  if (tok=="UP")            { kc = KEY_UP_ARROW; return true; }
  if (tok=="DOWN")          { kc = KEY_DOWN_ARROW; return true; }

  if (tok=="PAGEUP")        { kc = KEY_PAGE_UP; return true; }
  if (tok=="PAGEDOWN")      { kc = KEY_PAGE_DOWN; return true; }
  if (tok=="HOME")          { kc = KEY_HOME; return true; }
  if (tok=="END")           { kc = KEY_END; return true; }
  if (tok=="INSERT")        { kc = KEY_INSERT; return true; }
  if (tok=="DELETE")        { kc = KEY_DELETE; return true; }

  if (tok=="F1")  { kc = KEY_F1; return true; }
  if (tok=="F2")  { kc = KEY_F2; return true; }
  if (tok=="F3")  { kc = KEY_F3; return true; }
  if (tok=="F4")  { kc = KEY_F4; return true; }
  if (tok=="F5")  { kc = KEY_F5; return true; }
  if (tok=="F6")  { kc = KEY_F6; return true; }
  if (tok=="F7")  { kc = KEY_F7; return true; }
  if (tok=="F8")  { kc = KEY_F8; return true; }
  if (tok=="F9")  { kc = KEY_F9; return true; }
  if (tok=="F10") { kc = KEY_F10; return true; }
  if (tok=="F11") { kc = KEY_F11; return true; }
  if (tok=="F12") { kc = KEY_F12; return true; }

  return false;
}

// pontuação simples via ASCII (sem numpad)
bool asciiPunctFromToken(const String &tok, char &out) {
  if (tok=="GRAVE")      { out='`'; return true; }
  if (tok=="MINUS")      { out='-'; return true; }
  if (tok=="EQUAL")      { out='='; return true; }
  if (tok=="LBRACKET")   { out='['; return true; }
  if (tok=="RBRACKET")   { out=']'; return true; }
  if (tok=="BACKSLASH")  { out='\\';return true; }
  if (tok=="SEMICOLON")  { out=';'; return true; }
  if (tok=="QUOTE")      { out='\'';return true; }
  if (tok=="COMMA")      { out=','; return true; }
  if (tok=="DOT")        { out='.'; return true; }
  if (tok=="SLASH")      { out='/'; return true; } // OBS: para comandos use KEY_SLASH_FIX
  if (tok=="SPACE")      { out=' '; return true; }
  return false;
}

// ======= mapeamento auxiliares =======
bool mapDigitDefine(char d, uint8_t &kc) {
  switch(d){
    case '0': kc=KEY_0; return true;
    case '1': kc=KEY_1; return true;
    case '2': kc=KEY_2; return true;
    case '3': kc=KEY_3; return true;
    case '4': kc=KEY_4; return true;
    case '5': kc=KEY_5; return true;
    case '6': kc=KEY_6; return true;
    case '7': kc=KEY_7; return true;
    case '8': kc=KEY_8; return true;
    case '9': kc=KEY_9; return true;
  }
  return false;
}

bool numpadFromToken(const String &tok, uint8_t &kc) {
  if (tok=="NUM0")     { kc = KEY_NUM_0;    return true; }
  if (tok=="NUM1")     { kc = KEY_NUM_1;    return true; }
  if (tok=="NUM2")     { kc = KEY_NUM_2;    return true; }
  if (tok=="NUM3")     { kc = KEY_NUM_3;    return true; }
  if (tok=="NUM4")     { kc = KEY_NUM_4;    return true; }
  if (tok=="NUM5")     { kc = KEY_NUM_5;    return true; }
  if (tok=="NUM6")     { kc = KEY_NUM_6;    return true; }
  if (tok=="NUM7")     { kc = KEY_NUM_7;    return true; }
  if (tok=="NUM8")     { kc = KEY_NUM_8;    return true; }
  if (tok=="NUM9")     { kc = KEY_NUM_9;    return true; }

  if (tok=="NUMDOT"   || tok=="NUM.") { kc = KEY_NUM_DOT;   return true; }
  if (tok=="NUMSLASH" || tok=="NUM/") { kc = KEY_NUM_SLASH; return true; }
  if (tok=="NUMSTAR"  || tok=="NUM*") { kc = KEY_NUM_STAR;  return true; }
  if (tok=="NUMMINUS" || tok=="NUM-") { kc = KEY_NUM_MINUS; return true; }
  if (tok=="NUMPLUS"  || tok=="NUM+") { kc = KEY_NUM_PLUS;  return true; }
  if (tok=="NUMENTER")               { kc = KEY_NUM_ENTER; return true; }

  return false;
}


bool mapLetterDefine(char c, uint8_t &kc) {
  if (c>='a' && c<='z') c = (char)(c - 'a' + 'A'); // normaliza
  switch(c){
    case 'A': kc=KEY_A; return true;
    case 'B': kc=KEY_B; return true;
    case 'C': kc=KEY_C; return true;
    case 'D': kc=KEY_D; return true;
    case 'E': kc=KEY_E; return true;
    case 'F': kc=KEY_F; return true;
    case 'G': kc=KEY_G; return true;
    case 'H': kc=KEY_H; return true;
    case 'I': kc=KEY_I; return true;
    case 'J': kc=KEY_J; return true;
    case 'K': kc=KEY_K; return true;
    case 'L': kc=KEY_L; return true;
    case 'M': kc=KEY_M; return true;
    case 'N': kc=KEY_N; return true;
    case 'O': kc=KEY_O; return true;
    case 'P': kc=KEY_P; return true;
    case 'Q': kc=KEY_Q; return true;
    case 'R': kc=KEY_R; return true;
    case 'S': kc=KEY_S; return true;
    case 'T': kc=KEY_T; return true;
    case 'U': kc=KEY_U; return true;
    case 'V': kc=KEY_V; return true;
    case 'W': kc=KEY_W; return true;
    case 'X': kc=KEY_X; return true;
    case 'Y': kc=KEY_Y; return true;
    case 'Z': kc=KEY_Z; return true;
  }
  return false;
}

// ---------- TAP ----------
void tapToken(const String &tokIn) {
  // IMPORTANTE: para comandos ("/...") NÃO upper-case o conteúdo
  String raw = tokIn; raw.trim();

  // (A) Se começar com '/', tratar como comando de texto:
  if (raw.startsWith("/")) {
    String rest = raw.substring(1); // remove '/'
    sendSlashCommand(rest, /*sendEnter=*/true);
    return;
  }

  // A partir daqui é tratamento de tecla/token (maiúsculo)
  String tok = raw; tok.toUpperCase();

  // 1) especiais
  uint8_t kc = 0;
  if (specialFromToken(tok, kc)) { pressRelease(kc); return; }

  // 1.1) NUMPAD (novo)
  if (numpadFromToken(tok, kc)) { pressRelease(kc); return; }

  // 2) NÚMEROS -> ASCII com 80/200 (você validou que funciona)
  if (tok.length()==1 && tok[0]>='0' && tok[0]<='9') {
    pressReleaseAscii(tok[0], 80, 200);
    return;
  }

  // 3) Letras (mantém comportamento padrão anterior)
  if (tok.length()==1 && tok[0]>='A' && tok[0]<='Z') {
    if (mapLetterDefine(tok[0], kc)) { pressRelease(kc); return; }
  }

  // 4) pontuação ASCII simples
  char ch = 0;
  if (asciiPunctFromToken(tok, ch)) { Keyboard.write((uint8_t)ch); return; }

  // 5) modificador isolado
  uint8_t mod = 0;
  if (modifierFromToken(tok, mod)) { pressRelease(mod); return; }

  // 6) fallback: literal
  Keyboard.print(tok);
}

// ---------- DOWN / UP ----------
void handleDown(const String &tokIn) {
  String tok = tokIn; tok.trim(); tok.toUpperCase();

  uint8_t mod=0;
  if (modifierFromToken(tok, mod)) { Keyboard.press(mod); return; }

  uint8_t kc=0;
  if (numpadFromToken(tok, kc)) { Keyboard.press(kc); return; }
 
  if (specialFromToken(tok, kc)) { Keyboard.press(kc); return; }

  if (tok.length()==1 && tok[0]>='0' && tok[0]<='9') { if (mapDigitDefine(tok[0], kc)) { Keyboard.press(kc); return; } }
  if (tok.length()==1 && tok[0]>='A' && tok[0]<='Z') { if (mapLetterDefine(tok[0], kc)) { Keyboard.press(kc); return; } }

  char ch=0;
  if (asciiPunctFromToken(tok, ch)) { Keyboard.press((uint8_t)ch); return; }
}

void handleUp(const String &tokIn) {
  String tok = tokIn; tok.trim(); tok.toUpperCase();

  uint8_t mod=0;
  if (modifierFromToken(tok, mod)) { Keyboard.release(mod); return; }

  uint8_t kc=0;
  if (specialFromToken(tok, kc)) { Keyboard.release(kc); return; }

  if (numpadFromToken(tok, kc)) { Keyboard.release(kc); return; }

  if (tok.length()==1 && tok[0]>='0' && tok[0]<='9') { if (mapDigitDefine(tok[0], kc)) { Keyboard.release(kc); return; } }
  if (tok.length()==1 && tok[0]>='A' && tok[0]<='Z') { if (mapLetterDefine(tok[0], kc)) { Keyboard.release(kc); return; } }

  char ch=0;
  if (asciiPunctFromToken(tok, ch)) { Keyboard.release((uint8_t)ch); return; }
}

// ---------- COMBO ----------
void handleCombo(const String &seqIn) {
  String seq = seqIn; seq.trim(); seq.toUpperCase();

  const int MAXK = 8;
  String parts[MAXK];
  int n=0;

  int start=0;
  while (start < (int)seq.length() && n < MAXK) {
    int plus = seq.indexOf('+', start);
    if (plus < 0) plus = seq.length();
    parts[n++] = seq.substring(start, plus);
    start = plus + 1;
  }

  uint8_t pressedMods[MAXK]; int pm=0;
  uint8_t pressedCodes[MAXK]; int pc=0;

  // press
  for (int i=0; i<n; ++i) {
    String tok = parts[i]; tok.trim();

    uint8_t mod=0;
    if (modifierFromToken(tok, mod)) { Keyboard.press(mod); pressedMods[pm++]=mod; continue; }

    uint8_t kc=0;
    if (specialFromToken(tok, kc)) { Keyboard.press(kc); pressedCodes[pc++]=kc; continue; }

    if (numpadFromToken(tok, kc)) { Keyboard.press(kc); pressedCodes[pc++]=kc; continue; }

    if (tok.length()==1 && tok[0]>='0' && tok[0]<='9') {
      if (mapDigitDefine(tok[0], kc)) { Keyboard.press(kc); pressedCodes[pc++]=kc; continue; }
    }
    if (tok.length()==1 && tok[0]>='A' && tok[0]<='Z') {
      if (mapLetterDefine(tok[0], kc)) { Keyboard.press(kc); pressedCodes[pc++]=kc; continue; }
    }

    char ch=0;
    if (asciiPunctFromToken(tok, ch)) { Keyboard.press((uint8_t)ch); pressedCodes[pc++]=(uint8_t)ch; }
  }
  delay(35);
  // release reverse
  for (int i=pc-1; i>=0; --i) Keyboard.release(pressedCodes[i]);
  for (int i=pm-1; i>=0; --i) Keyboard.release(pressedMods[i]);
}

// ---------- parser serial ----------
void processLine(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) { Serial.println("OK"); return; }

  // TYPE: se começar com '/', trata como comando usando KEY_SLASH_FIX
  if (cmd.startsWith("TYPE:")) {
    String payload = cmd.substring(5); payload.trim();
    if (payload.startsWith("/")) {
      sendSlashCommand(payload.substring(1), /*sendEnter=*/true);
      Serial.println("OK");
      return;
    }
    typeText(payload);
    Serial.println("OK");
    return;
  }

  // TAP: aceita também "/..." como comando
  if (cmd.startsWith("TAP:"))  { tapToken(cmd.substring(4));  Serial.println("OK"); return; }
  if (cmd.startsWith("DOWN:")) { handleDown(cmd.substring(5));Serial.println("OK"); return; }
  if (cmd.startsWith("UP:"))   { handleUp(cmd.substring(3));  Serial.println("OK"); return; }
  if (cmd.startsWith("COMBO:")){ handleCombo(cmd.substring(6));Serial.println("OK"); return; }

  Serial.println("OK"); // default
}

// ---------- setup/loop ----------
void setup() {
  Serial.begin(115200);
  delay(500);
  Keyboard.begin();
}

void loop() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      processLine(line);
      line = "";
    } else {
      if (line.length() < 512) line += c;
    }
  }
}
