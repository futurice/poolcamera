/*
  Sends a signal via serial if the button is pressed, includes debounce
*/

const int BUTTON = 2;

bool currentState = false;
bool lastState = false;
bool timerActive = false;

unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 42; //buffer time to prevent false readings

unsigned long lastPressTime = 0;
unsigned long pressDelay = 1952; //How many millis before sending the signal

void setup() {
  pinMode(BUTTON, INPUT_PULLUP);
  Serial.begin(9600);
}

void loop() {
  
  int buttonState = digitalRead(BUTTON);

  if (buttonState != lastState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
 
    if (buttonState != currentState) {
      currentState = buttonState;

      if (buttonState == true) {
        timerActive = true;
        lastPressTime = millis();
        
        //
      }
    }
  }

  if(timerActive && (millis() - lastPressTime) > pressDelay) {
    Serial.println('a'); //We send an a, because reasons.
    timerActive = false;
  }

  lastState = buttonState;
}
