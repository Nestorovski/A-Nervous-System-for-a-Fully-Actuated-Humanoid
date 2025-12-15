import logging
from typing import Dict, Any, Optional

logger = logging.getLogger('inmoov_v13')

class ProtocolTranslator:
    """
    Translates GUI actuator commands to Arduino distributed protocol v2.3.
    """

    def __init__(self):
        # Mappings stored for reference
        self.servo_mappings = {'SERVO1': 6, 'SERVO2': 7, 'SERVO3': 14, 'SERVO4': 15}

    def translate_servo_command(self, actuator_id: int, angle: float, config: Dict[str, Any]) -> Optional[str]:
        """
        Generates command for SG90 Servos (Absolute Position).
        Format: PORT:SET_SERVOx:ANGLE
        """
        try:
            mux_port = config.get('mux_port', 0)
            name = config.get('name', 'SERVO1')
            angle = int(max(0, min(180, angle)))
            return f"{mux_port}:SET_{name}:{angle}"
        except Exception as e:
            logger.error(f"Servo translation error ID {actuator_id}: {e}")
            return None

    def translate_motor_raw(self, actuator_id: int, speed: float, config: Dict[str, Any]) -> Optional[str]:
        """
        Generates N20 Motor command (Raw Speed/Direction).
        Format: PORT:TEST_MOTORx_DIR:DUTY
        """
        try:
            mux_port = config.get('mux_port', 0)
            name = config.get('name', 'MOTOR1A')
            
            direction = "FWD" if speed >= 0 else "REV"
            duty = int(abs(speed))
            duty = max(0, min(100, duty))
            
            return f"{mux_port}:TEST_{name}_{direction}:{duty}"
        except Exception as e:
            logger.error(f"Motor translation error ID {actuator_id}: {e}")
            return None

    def translate_scan(self):
        return "SCAN:SYSTEM"

    def translate_i2c_scan(self, mux_port):
        prefix = str(mux_port) if mux_port is not None else "D"
        return f"{prefix}:SCAN_I2C"

    def translate_pots_read(self, mux_port=None):
        prefix = str(mux_port) if mux_port is not None else "D"
        return f"{prefix}:TEST_POTS"

    def parse_telemetry(self, line: str) -> Dict[str, Any]:
        telemetry = {}
        try:
            if line.startswith("POTS:"):
                values = line[5:].split(',')
                telemetry['pots'] = [int(v) for v in values if v.strip().lstrip('-').isdigit()]
            elif line.startswith("I2C_SCAN:"):
                telemetry['i2c_addresses'] = [addr.strip() for addr in line.split(':')[1].split(',') if addr.strip()]
            elif line.startswith("FOUND:"):
                telemetry['topology'] = line.split(':')[1].strip()
            elif line == "CMD_OK":
                telemetry['command_ack'] = True
        except Exception as e:
            logger.error(f"Telemetry parsing error: {e}")
        return telemetry