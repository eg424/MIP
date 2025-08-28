// HX Pin Assignments
const int en_R_HX = 24;
const int en_L_HX = 25;
const int PWM_R_HX = 4;
const int PWM_L_HX = 5;

// HX Calibration Parameters
const float HX_slope = 0.0406;
const float HX_intercept = 0;
const float HX_I_co = 1.035;

// HY Pin Assignments
const int en_R_HY = 44;
const int en_L_HY = 45;
const int PWM_R_HY = 6;
const int PWM_L_HY = 7;

// HY Calibration Parameters
const float HY_intercept = 0.04;
const float HY_I_co = 1.1;
const float HY_slope = 0.04296;

// MX Pin Assignments
const int en_R_MX = 22;
const int en_L_MX = 23;
const int PWM_R_MX = 2;
const int PWM_L_MX = 3;

// MX Calibration Parameters
const float MX_slope = 0.03504;
const float MX_intercept = 0.009;
const float MX_I_co = 0.95;

// MY Pin Assignments
const int en_R_MY = 46;
const int en_L_MY = 47;
const int PWM_R_MY = 8;
const int PWM_L_MY = 9;

// MY Calibration Parameters
const float MY_slope = 0.0177;
const float MY_intercept = 0.03;
const float MY_I_co = 1.73;

// Set pins as outputs and enable
void setup() {
  pinMode(en_R_HX, OUTPUT);
  pinMode(en_L_HX, OUTPUT);
  pinMode(PWM_R_HX, OUTPUT);
  pinMode(PWM_L_HX, OUTPUT);
  digitalWrite(en_R_HX, HIGH);
  digitalWrite(en_L_HX, HIGH);

  pinMode(en_R_HY, OUTPUT);
  pinMode(en_L_HY, OUTPUT);
  pinMode(PWM_R_HY, OUTPUT);
  pinMode(PWM_L_HY, OUTPUT);
  digitalWrite(en_R_HY, HIGH);
  digitalWrite(en_L_HY, HIGH);
  
  pinMode(en_R_MX, OUTPUT);
  pinMode(en_L_MX, OUTPUT);
  pinMode(PWM_R_MX, OUTPUT);
  pinMode(PWM_L_MX, OUTPUT);
  digitalWrite(en_R_MX, HIGH);
  digitalWrite(en_L_MX, HIGH);

  pinMode(en_R_MY, OUTPUT);
  pinMode(en_L_MY, OUTPUT);
  pinMode(PWM_R_MY, OUTPUT);
  pinMode(PWM_L_MY, OUTPUT);
  digitalWrite(en_R_MY, HIGH);
  digitalWrite(en_L_MY, HIGH);

  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();  // Remove any whitespace

    // Parse input string into 4 float values (currents)
    float currents[4];
    int index = 0;
    int startIndex = 0;
    int endIndex = input.indexOf(',');

    while (endIndex != -1 && index < 4) {
      currents[index++] = input.substring(startIndex, endIndex).toFloat();
      startIndex = endIndex + 1;
      endIndex = input.indexOf(',', startIndex);
    }

    // Handle last value after the final comma
    if (index < 4) {
      currents[index++] = input.substring(startIndex).toFloat();
    }

    // If all 4 values were successfully parsed, update coil currents
    if (index == 4) {
      setCoilCurrents(currents[0], currents[1], currents[2], currents[3]);
    } else {
      Serial.println("Invalid input format");
    }
  }
}

// Current to PWM using slope and intercept
float calculatePWM(float current, float slope, float intercept) {
  if (current == 0) return 0;

  float pwmValue = (current - intercept) / slope;
  pwmValue = constrain(pwmValue, 0, 255);  // Clamp between 0–255
  return pwmValue;
}

// Set desired current for all 4 coils
void setCoilCurrents(float currentMX, float currentHX, float currentMY, float currentHY) {
  setSingleCoilCurrent(PWM_R_MX, PWM_L_MX, currentMX * MX_I_co, MX_slope, MX_intercept, "MX");
  setSingleCoilCurrent(PWM_R_HX, PWM_L_HX, currentHX * HX_I_co, HX_slope, HX_intercept, "HX");
  setSingleCoilCurrent(PWM_R_MY, PWM_L_MY, currentMY * MY_I_co, MY_slope, MY_intercept, "MY");
  setSingleCoilCurrent(PWM_R_HY, PWM_L_HY, currentHY * HY_I_co, HY_slope, HY_intercept, "HY");
}

// Set current for a single coil (bidirectional control)
void setSingleCoilCurrent(int pinR, int pinL, float desiredCurrent, float slope, float intercept, String coilName) {
  bool isForward = desiredCurrent > 0;
  float adjustedCurrent = abs(desiredCurrent);
  float rawPWM = (adjustedCurrent - intercept) / slope;
  float pwmValue = constrain(rawPWM, 0, 255);

  Serial.print(coilName);
  Serial.print(" PWM Value: ");
  Serial.println(pwmValue);

  // PWM direction by writing to left/right pins
  if (isForward) {
    analogWrite(pinL, pwmValue);
    analogWrite(pinR, 0);
  } else {
    analogWrite(pinL, 0);
    analogWrite(pinR, pwmValue);
  }
}
