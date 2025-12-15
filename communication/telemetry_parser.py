import logging
from typing import Dict, Any, List, Optional
from PyQt6.QtCore import QObject

logger = logging.getLogger('inmoov_v12')

class TelemetryParser(QObject):
    """
    Parses and processes telemetry data from Arduino distributed system.
    
    This class handles the string parsing logic. It returns structured data 
    dictionaries to be emitted by the SerialManager.
    """

    def __init__(self):
        super().__init__()
        self.last_pots = {}

    def parse_line(self, line: str) -> Dict[str, Any]:
        """
        Parse a single line of telemetry data.

        Args:
            line: Raw line from serial port

        Returns:
            Dictionary containing parsed data (e.g., {'pots': [1, 2, 3, 4]})
        """
        if not line or not line.strip():
            return {}

        line = line.strip()
        telemetry = {}

        try:
            # Parse based on known formats
            if line.startswith("POTS:"):
                telemetry.update(self._parse_pots(line))
            elif line.startswith("I2C_SCAN:"):
                telemetry.update(self._parse_i2c_scan(line))
            elif line.startswith("FOUND:"):
                telemetry.update(self._parse_topology(line))
            elif line == "CMD_OK":
                telemetry['command_ack'] = "CMD_OK"
            elif line == "CALIB_DONE":
                telemetry['command_ack'] = "CALIB_DONE"
            # We can ignore PID debug lines or add them if needed
            
        except Exception as e:
            logger.error(f"Telemetry parsing error for line '{line}': {e}")

        return telemetry

    def _parse_pots(self, line: str) -> Dict[str, List[int]]:
        """
        Parse potentiometer readings: POTS:val1,val2,val3,val4

        Returns dict with 'pots' key containing list of int values
        """
        try:
            # Remove "POTS:" prefix
            values_str = line[5:]
            if not values_str:
                return {}

            values = []
            for val_str in values_str.split(','):
                val_str = val_str.strip()
                # Ensure it's a valid integer (handles negative values too)
                if val_str and (val_str.isdigit() or (val_str.startswith('-') and val_str[1:].isdigit())):
                    values.append(int(val_str))

            if values:
                # Return standard list format
                return {'pots': values}

        except ValueError as e:
            logger.error(f"Invalid pot values in line: {line} - {e}")

        return {}

    def _parse_i2c_scan(self, line: str) -> Dict[str, List[str]]:
        """
        Parse I2C scan results: I2C_SCAN:0x40,0x48,0x70

        Returns dict with 'i2c_addresses' key containing list of hex strings
        """
        try:
            # Remove "I2C_SCAN:" prefix
            # Use split in case prefix length varies, though fixed index is faster
            parts = line.split(":", 1)
            if len(parts) < 2:
                return {}
            
            addresses_str = parts[1]
            if not addresses_str:
                return {}

            addresses = [addr.strip() for addr in addresses_str.split(',') if addr.strip()]

            if addresses:
                return {'i2c_addresses': addresses}

        except Exception as e:
            logger.error(f"Invalid I2C scan format in line: {line} - {e}")

        return {}

    def _parse_topology(self, line: str) -> Dict[str, str]:
        """
        Parse topology information: FOUND:Direct (No Mux) or FOUND:Port 0

        Returns dict with 'topology' key containing the found device info
        """
        try:
            # Remove "FOUND:" prefix
            parts = line.split(":", 1)
            if len(parts) < 2:
                return {}
                
            info = parts[1].strip()
            if info:
                return {'topology': info}

        except Exception as e:
            logger.error(f"Invalid topology format in line: {line} - {e}")

        return {}

    def validate_telemetry_format(self, expected_format: str, line: str) -> bool:
        """
        Validate that a telemetry line matches expected format.
        """
        return line.startswith(expected_format)