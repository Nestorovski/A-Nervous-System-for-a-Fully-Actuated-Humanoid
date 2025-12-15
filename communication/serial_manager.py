import serial
import serial.tools.list_ports
import threading
import queue
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from .telemetry_parser import TelemetryParser
from .protocol_translator import ProtocolTranslator

logger = logging.getLogger('inmoov_v12')

class SerialManager(QObject):
    """Hardware communication manager for InMoov distributed system"""

    # Signals for telemetry data
    # CHANGED: pots_updated now emits a list [val1, val2...] to match Parser output
    pots_updated = pyqtSignal(list)       
    i2c_scan_complete = pyqtSignal(list)  # [addresses]
    topology_updated = pyqtSignal(str)    # topology info
    command_acknowledged = pyqtSignal(str)# command type
    raw_log_received = pyqtSignal(str)    # For debugging console

    def __init__(self):
        super().__init__()  # Initialize QObject base class
        self.ser = None
        self.connected = False
        self._send_q = queue.Queue()
        self._stop_event = threading.Event()
        self._worker = None
        self.telemetry_parser = TelemetryParser()
        self.protocol_translator = ProtocolTranslator()

    def connect(self, port):
        """Connect to serial port"""
        try:
            # Reduced timeout slightly for snappier reading
            self.ser = serial.Serial(port, 115200, timeout=0.05)
            self.connected = True
            self._stop_event.clear()
            # start worker thread to handle reads/writes
            self._worker = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker.start()
            logger.info(f"Connected to {port}")
            return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from serial port"""
        self.connected = False
        try:
            self._stop_event.set()
            if self.ser:
                # Force close logic
                try:
                    self.ser.cancel_read()
                    self.ser.cancel_write()
                except:
                    pass
                self.ser.close()
            
            if self._worker and self._worker.is_alive():
                self._worker.join(timeout=0.5)
        except Exception as e:
            logger.debug(f"Disconnect cleanup error: {e}")
        finally:
            self.ser = None

    def send(self, board, pin, val):
        """Send command using old protocol format (Legacy support)"""
        if self.connected:
            msg = f"<{board}:{pin}:{val}>\n"
            try:
                self._send_q.put_nowait(msg)
            except queue.Full:
                logger.warning('Send queue full, dropping message')

    def send_raw(self, command):
        """Send raw command string"""
        if self.connected:
            try:
                # Ensure newline
                cmd = command.strip() + "\n"
                self._send_q.put_nowait(cmd)
            except queue.Full:
                logger.warning('Send queue full, dropping message')

    def send_actuator_command(self, actuator_id: int, value: float,
                             actuator_config: dict):
        """
        Send command for an actuator using protocol translation.
        """
        try:
            command = self.protocol_translator.translate_command(
                actuator_id, value, actuator_config
            )
            if command:
                self.send_raw(command)
                logger.debug(f"Sent actuator command: {command}")
            else:
                logger.error(f"Failed to translate command for actuator {actuator_id}")
        except Exception as e:
            logger.error(f"Error sending actuator command: {e}")

    def enable_stream(self, enable):
        """
        Enable/disable telemetry streaming.
        Note: Firmware v2.2 typically requires polling via TEST_POTS, 
        but we keep this in case future firmware supports auto-streaming.
        """
        if self.connected:
            cmd = "STREAM_ON\n" if enable else "STREAM_OFF\n"
            try:
                self._send_q.put_nowait(cmd)
            except queue.Full:
                logger.debug('Stream command queue full')

    def _worker_loop(self):
        """Background thread: drain send queue and read incoming lines."""
        while not self._stop_event.is_set():
            if not self.ser or not self.ser.is_open:
                self.connected = False
                break
            
            # 1. Drain outgoing queue
            try:
                while not self._send_q.empty():
                    msg = self._send_q.get_nowait()
                    try:
                        self.ser.write(msg.encode())
                    except Exception as e:
                        logger.debug(f'Error writing serial: {e}')
                        self.connected = False
                        break
            except queue.Empty:
                pass
            
            # 2. Read incoming data
            try:
                if self.ser and self.ser.in_waiting:
                    line = self.ser.readline().decode(errors='ignore').strip()
                    if line:
                        # Log raw for debugging
                        self.raw_log_received.emit(line)

                        # Parse telemetry using the parser
                        telemetry = self.telemetry_parser.parse_line(line)
                        if telemetry:
                            # Emit appropriate signals based on telemetry type
                            if 'pots' in telemetry:
                                self.pots_updated.emit(telemetry['pots'])
                            if 'i2c_addresses' in telemetry:
                                self.i2c_scan_complete.emit(telemetry['i2c_addresses'])
                            if 'topology' in telemetry:
                                self.topology_updated.emit(telemetry['topology'])
                            if 'command_ack' in telemetry:
                                self.command_acknowledged.emit(telemetry['command_ack'])
            except Exception as e:
                logger.debug(f'Error reading serial: {e}')
                # Don't break loop immediately on read error, give it a chance to recover
            
            # Small sleep to yield CPU
            self._stop_event.wait(0.005)

    # Removed read_loop() entirely as it conflicts with _worker_loop