.. -*- mode: rst -*-

0.4.1
~~~~~

- Add ssc32yaml script runner
- Don't change servo position on init (`Servo.is_changed` flag)


0.4.0
~~~~~

- Servo script interface
  with YAML serialization/deserialization
- Move to package
- Depends on PyYAML


0.3.3
~~~~~

- Rename Servo properties `Servo.degree` -> `Servo.degrees`, `Servo.radian` -> `Servo.radians`
- Use callback for Servo
- Description for configuration (`SSC32.description`) line starts with `#~`
