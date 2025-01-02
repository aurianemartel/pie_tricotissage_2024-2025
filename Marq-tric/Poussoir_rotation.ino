
#define BUTTON_PIN 2   // Broche numérique pour le bouton poussoir
#define RELAY_PIN1 10   // Broche numérique pour le relais 1

bool relayState = false;  // État initial du relais

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);  // Configuration du bouton poussoir en entrée avec résistance de pull-up interne
  pinMode(RELAY_PIN1, OUTPUT);         // Configuration du relais en sortie
  digitalWrite(RELAY_PIN1, LOW);       // Initialisation du relais à l'état bas
}

void loop() {
  // Lecture de l'état du bouton poussoir
  int buttonState = digitalRead(BUTTON_PIN);

  // Si le bouton est enfoncé et que le relais n'est pas déjà activé
  if (buttonState == LOW && !relayState) {
    // Activer le relais
    digitalWrite(RELAY_PIN1, HIGH);
    relayState = true;
  } 
  // Si le bouton est relâché et que le relais est activé
  else if (buttonState == HIGH && relayState) {
    // Désactiver le relais
    digitalWrite(RELAY_PIN1, LOW);
    relayState = false;
  }
}