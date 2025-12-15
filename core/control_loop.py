import logging
from PyQt6.QtCore import QObject, QTimer

logger = logging.getLogger('inmoov_v13')

class BangBangController(QObject):
    """
    Python-side Logic Controller for N20 Motors.
    Replaces the firmware loop to allow distributed control.
    """
    
    def __init__(self, serial_manager, config_manager):
        super().__init__()
        self.serial = serial_manager
        self.config = config_manager
        
        self.active = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._control_tick)
        
        # State Storage
        self.targets = {}       # {joint_id: target_angle_deg}
        self.current_pots = {}  # {joint_id: raw_pot_val}
        self.last_command = {}  # {joint_id: "FWD"|"REV"|"STOP"}
        
        # Load initial values from Config
        self._update_params()
        
        # LISTEN for changes! (The Explosion)
        self.config.preference_changed.connect(self._on_pref_changed)

    def _on_pref_changed(self, key, value):
        """Reacts instantly to settings changes."""
        if key in ["motor_max_speed", "motor_tolerance"]:
            self._update_params()
            logger.info(f"Controller updated {key} to {value}")

    def _update_params(self):
        """Reads Governor limits from config."""
        self.motor_speed = self.config.get("motor_max_speed") or 80
        self.tolerance = self.config.get("motor_tolerance") or 15

    def start(self):
        if not self.active:
            self.active = True
            self.timer.start(50) # 20Hz Control Loop
            logger.info("Bang-Bang Controller Started")

    def stop(self):
        self.active = False
        self.timer.stop()
        self._stop_all_motors()
        logger.info("Bang-Bang Controller Stopped")

    def set_target(self, joint_id, angle):
        """Called when user moves slider."""
        self.targets[str(joint_id)] = float(angle)
        if not self.active:
            self.start()

    def update_sensors(self, pot_data, mux_context=0):
        # Find which joints are on the active Mux Port
        # Note: mux_context handling needs to be robust in main loop
        # For now, we iterate all mapped hardware
        for jid, hw in self.config.hardware_map.items():
            # In a real distributed read, we'd check if hw.mux_port == mux_context
            # Here we assume data flow is handled correctly upstream or just map by channel
            ads_ch = hw.get('ads_channel')
            if ads_ch is not None and isinstance(pot_data, list) and ads_ch < len(pot_data):
                self.current_pots[jid] = pot_data[ads_ch]

    def _control_tick(self):
        """The Main Logic Loop (Runs 20 times/sec)"""
        if not self.active: return

        # Iterate through all joints we have targets for
        for jid, target_angle in self.targets.items():
            
            if jid not in self.current_pots: continue
            current_pot = self.current_pots[jid]
            
            hw = self.config.get_pin_config(jid)
            if hw.get('motor_type') != 'n20': continue 
            
            # Map Angle -> Target Pot Value
            min_pot = hw.get('min_ana', 0)
            max_pot = hw.get('max_ana', 1023)
            min_ang = hw.get('angle_min', 0)
            max_ang = hw.get('angle_max', 180)
            
            if (max_ang - min_ang) == 0: continue
            
            target_pot = min_pot + (target_angle - min_ang) * (max_pot - min_pot) / (max_ang - min_ang)
            
            error = target_pot - current_pot
            
            command_speed = 0
            if abs(error) > self.tolerance:
                # GOVERNOR CHECK: Use the dynamic motor_speed from settings
                if error > 0:
                    command_speed = self.motor_speed  
                else:
                    command_speed = -self.motor_speed 
            
            self._send_if_changed(jid, command_speed, hw)

    def _send_if_changed(self, jid, speed, hw_config):
        state_key = "STOP"
        if speed > 0: state_key = "FWD"
        if speed < 0: state_key = "REV"
        
        last = self.last_command.get(jid, None)
        
        if state_key != last:
            cmd_str = self.serial.protocol_translator.translate_motor_raw(int(jid), speed, hw_config)
            if cmd_str:
                self.serial.send_raw(cmd_str)
                self.last_command[jid] = state_key

    def _stop_all_motors(self):
        # Iterate all active motors and send stop
        for jid in self.last_command:
            if self.last_command[jid] != "STOP":
                hw = self.config.get_pin_config(jid)
                cmd = self.serial.protocol_translator.translate_motor_raw(int(jid), 0, hw)
                if cmd: self.serial.send_raw(cmd)
        self.last_command.clear()