#include <DmxSimple.h>

/* bauds rate */
#define BAUDS 115200
/* Total number of channels */
/* belt, stamp1, stamp2, blow */
#define NUM_CHANNELS 4
/* Belt running time in milliseconds */
#define BELT_RUNNING_TIME 30000
/* stamp 1 blow time in milliseconds */
#define STAMP_1_TIME 80
/* stamp2 blow time in milliseconds */
#define STAMP_2_TIME 80
/* Blow time in milliseconds */
#define BLOW_TIME 1000

#define IGNORE_TIME 8500
/* DMX pin */
#define DMX_PIN 3
/* IR pin */
//#define IR_PIN 6

#define ARMED 8
#define UNARMED 9

unsigned long STAMP_WAITING_TIME_1 = 6000;
unsigned long STAMP_WAITING_TIME_2 = 7000;
unsigned long STAMP_TO_BLOW_TIME = 3500;
unsigned long SECURITY_TIMER = 120000;

int counter = 0;
int count = 0;
int old_count = 0;
int clas = 0;
unsigned long belt_timer;
unsigned long stamp_1_timer;
unsigned long stamp_2_timer;
unsigned long blower_timer;
unsigned long ir_timer;
unsigned long print_timer;
unsigned long stamp_1_to_blow;
bool ir_aware = false;
bool printing_class_1 = false;
bool printing_class_2 = false;
bool stamp_to_blow = false;
bool belt_running = false;
bool stamp_1_stamping = false;
bool stamp_2_stamping = false;
bool blower_blowing = false;

void start_belt() {
  DmxSimple.write(1, 255);
  belt_running = true;
  counter++;
  belt_timer = millis();
}

void stop_belt()  {
  counter--;
  if (counter <= 0) {
    DmxSimple.write(1, 0);
    counter = 0;
    belt_running = false;
  }
}

void start_stamp_1() {
  DmxSimple.write(2, 255);
  stamp_1_stamping = true;
  stamp_1_timer = millis();
}

void stop_stamp_1() {
  DmxSimple.write(2, 0);
  stamp_1_stamping = false;
}

void start_stamp_2() {
  DmxSimple.write(3, 255);
  stamp_2_stamping = true;
  stamp_2_timer = millis();
}

void stop_stamp_2() {
  DmxSimple.write(3, 0);
  stamp_2_timer = false;
}

void blow() {
  DmxSimple.write(4, 255);
  blower_blowing = true;
  blower_timer = millis();
}

void stop_blowing() {
  DmxSimple.write(4, 0);
  blower_blowing = false;
}

void debug_blow() {
  DmxSimple.write(4, 255);
}

void setup() {
  DmxSimple.usePin(3);
//  pinMode(6, INPUT);
  Serial.begin(115200);
  DmxSimple.maxChannel(NUM_CHANNELS);
  for (int i = 1; i <= NUM_CHANNELS; i++) {
    DmxSimple.write(i, 0);
  }
}

void loop() {
  /*
  Stop actions after determined time
  because no fcking threads :-(
  */
  unsigned long now = millis();
//  if (belt_running && ((now - belt_timer) > BELT_RUNNING_TIME)) stop_belt();
  if (stamp_1_stamping && ((now - stamp_1_timer) > STAMP_1_TIME)) stop_stamp_1();
  if (stamp_2_stamping && ((now - stamp_2_timer) > STAMP_2_TIME)) stop_stamp_2();
  if (blower_blowing && ((now - blower_timer) > BLOW_TIME)) stop_blowing();

  /*
  Read inputs from serial /dev/tty.usbserial-A100RQM4 
  at 115200 bauds
  */
  if (Serial.available()) {
    char in_byte = Serial.read();
    switch(in_byte) {
      case '1':
        start_belt();
        break; 
      case '2':
        start_stamp_1();
        break;
      case '3':
        start_stamp_2();
        break;
      case '4':
        blow();
        break;
      case '5':
        stop_belt();  
        break;
      case '6':
        debug_blow();
        break;
      case '7':
        stop_blowing();
        break;
      case '8':
        start_belt();
        clas = 8;
        printing_class_1 = true;
        break;
      case '9':
        start_belt();
        clas = 9;
        printing_class_2 = true;
        break;   
      default:
        break;
    }
  }
}



