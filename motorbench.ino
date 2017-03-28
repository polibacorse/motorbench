/*
 * Motor Sensors Reading for Arduino Uno MEGA
 * Copyright (c) Poliba Corse. All rights reserved.
 */

/*
 * PINS PLACEMENT
 * Air flow   A0
 * Encoder    A1
 * Pressure   A2
 * Distance   A3
 */

// readings
float flowRead  = 0.0;
float encRead   = 0.0;
float pressRead = 0.0;
float distRead  = 0.0;
float value     = 0.0;

// delay setup
const int DELAY = 333;

void setup() {
  //PINS ASSEIGNEMENT
  pinMode(A0,INPUT);
  pinMode(A1,INPUT);
  pinMode(A2,INPUT);
  pinMode(A3,INPUT);

  //START SERIAL COMMUNICATION (CONST BAUDRATE 9600)  
  Serial.begin(9600);
}
  
void loop() {
  String reading="";

  encRead = get_enc_reading(analogRead(A1));
  Serial.println('E' + (String) encRead);

  flowRead = get_flow_reading(analogRead(A0));
  Serial.println('F' + (String) flowRead);

  pressRead = get_press_reading(analogRead(A2));
  Serial.println('P' + (String) pressRead);

  //distRead = get_dist_reading(analogRead(A3));
  //Serial.println((String) distRead);

  delay(DELAY);
}

float get_flow_reading(float reading)
{
  //air flow sensor (quadratic polynomial curve)
  // Unit: kg/h
  float v_IN = (reading * 5) / 1023;
  return  - 10.3268
          - 70.8735 * v_IN
          + 153.347 * v_IN * v_IN 
          - 95.6418 * v_IN * v_IN * v_IN 
          + 27.3203 * v_IN * v_IN * v_IN * v_IN 
          -  2.4999 * v_IN * v_IN * v_IN * v_IN * v_IN;
}

float get_enc_reading(float reading)
{
  // Encoder (linearity 0.5% FS)
  // Unit: degrees
  float offsetCode = 102.0; // codice da togliere per considerare l'offset di 0.5V
  reading = reading - offsetCode;
  // conversion into degrees 360:921 = x: reading
  // value = reading*360/1024;//921;
  value = reading * 360 / 819.2;
  return value;
}

float get_press_reading(float reading)
{
  // Pressure (approximatively linear) - 0.25:4.75 => 17:105 kPa
  // Unit: kPa
  float offsetCode = 51.0; // codice da togliere per considerare l'offset di 0.5V   
  reading = reading - offsetCode;
  return (reading * 88 / 927) + 17;
}

float get_dist_reading(float reading)
{
  // distance (linear?) 
  // offset code => 300?
  return reading * 26 / 1024;
}

