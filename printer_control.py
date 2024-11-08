import serial
import time
import json
import logging
from queue import Queue
import random
from dataclasses import dataclass
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


@dataclass
class PrinterConfig:
    port: str
    baudrate: int
    move_increment: int
    extrude_amount: float
    extrude_temp: int
    feed_rate: int
    max_dimensions: Dict[str, int]
    logfile: str
    max_queue_size: int
    simulation: Dict[str, Any]


class BasePrinter(ABC):
    def __init__(self, config: PrinterConfig):
        self.config = config
        self.x_pos = self.y_pos = self.z_pos = 0
        self.command_queue = Queue(maxsize=config.max_queue_size)
        self.total_filament = 0
        self.running = True
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create a file handler for printer-specific logs
        printer_handler = logging.FileHandler(self.config.logfile)
        printer_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        # Remove any existing handlers and add the new one
        self.logger.handlers = []
        self.logger.addHandler(printer_handler)

        # Don't propagate logs to the root logger to avoid duplicate logging
        self.logger.propagate = False

        # Set the log level (you can adjust this as needed)
        self.logger.setLevel(logging.INFO)

    @abstractmethod
    def setup_printer(self):
        pass

    @abstractmethod
    def send_gcode(self, command: str) -> str:
        pass

    @abstractmethod
    def heat_hotend(self, target_temp: int):
        pass

    def validate_position(self, x: Optional[float] = None, y: Optional[float] = None,
                          z: Optional[float] = None) -> tuple:
        max_dim = self.config.max_dimensions
        new_x = min(max(0, x), max_dim['x']) if x is not None else self.x_pos
        new_y = min(max(0, y), max_dim['y']) if y is not None else self.y_pos
        new_z = min(max(0, z), max_dim['z']) if z is not None else self.z_pos
        return new_x, new_y, new_z

    def move(self, x: Optional[float] = None, y: Optional[float] = None,
             z: Optional[float] = None, extrude: bool = False) -> None:
        new_x, new_y, new_z = self.validate_position(x, y, z)

        if all(curr == new for curr, new in
               zip([self.x_pos, self.y_pos, self.z_pos], [new_x, new_y, new_z])):
            return

        command = f"G{'1' if extrude else '0'} "
        updates = []

        for axis, pos, new_pos in [('X', self.x_pos, new_x),
                                   ('Y', self.y_pos, new_y),
                                   ('Z', self.z_pos, new_z)]:
            if pos != new_pos:
                updates.append(f"{axis}{new_pos}")

        if updates:
            command += " ".join(updates)
            if extrude:
                command += f" E{self.config.extrude_amount}"
                self.total_filament -= self.config.extrude_amount
            command += f" F{self.config.feed_rate}"
            self.logger.info(f"Sending command {command}")
            self.send_gcode(command)

            self.x_pos, self.y_pos, self.z_pos = new_x, new_y, new_z

    def process_command(self, command: str, extrude: bool = False) -> None:
        movement_map = {
            "back": (None, self.y_pos + self.config.move_increment, None),
            "forward": (None, self.y_pos - self.config.move_increment, None),
            "left": (self.x_pos - self.config.move_increment, None, None),
            "right": (self.x_pos + self.config.move_increment, None, None),
            "up": (None, None, self.z_pos + self.config.move_increment),
            "down": (None, None, self.z_pos - self.config.move_increment)
        }

        if command in movement_map:
            self.move(*movement_map[command], extrude=extrude)

    def run(self) -> None:
        self.logger.info("Starting printer control loop")
        while self.running:
            try:
                if not self.command_queue.empty():
                    command = self.command_queue.get()
                    should_extrude = self.total_filament >= self.config.extrude_amount
                    self.process_command(command, extrude=should_extrude)
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in printer control loop: {e}")

    def stop(self) -> None:
        self.logger.info("Stopping printer")
        self.running = False


class RealPrinter(BasePrinter):
    def setup_printer(self):
        self.serial = serial.Serial(
            self.config.port,
            self.config.baudrate,
            timeout=1
        )
        self.serial.flushInput()
        self.serial.flushOutput()

        self.heat_hotend(self.config.extrude_temp)

        self.home()
        self.move(
            x=self.config.max_dimensions['x'] // 2,
            y=self.config.max_dimensions['y'] // 2,
            z=self.config.max_dimensions['z'] // 4
        )

    def send_gcode(self, command: str) -> str:
        self.logger.debug(f"Sending command: {command}")
        self.serial.write(f"{command}\n".encode())
        self.serial.flush()
        return self.await_response()

    def await_response(self) -> str:
        while True:
            response = self.serial.readline().decode().strip()
            if response:
                self.logger.debug(f"Printer response: {response}")
            if response.startswith("ok"):
                break
        return response

    def heat_hotend(self, target_temp: int) -> None:
        self.logger.info(f"Heating hotend to {target_temp}°C")
        self.send_gcode(f"M104 S{target_temp}")
        while True:
            response = self.send_gcode("M105")
            if "T:" in response:
                current_temp = float(response.split("T:")[1].split()[0])
                self.logger.debug(f"Current hotend temperature: {current_temp}°C")
                if current_temp >= target_temp:
                    self.logger.info("Hotend reached target temperature")
                    break
            time.sleep(1)

    def home(self) -> None:
        self.logger.info("Homing printer")
        self.send_gcode("G28")
        self.x_pos = self.y_pos = self.z_pos = 0
        self.send_gcode("M83")  # Set extruder to relative mode


class SimulatedPrinter(BasePrinter):
    def setup_printer(self):
        self.hotend_temp = 0
        self.logger.info("Simulated printer initialized")
        self.heat_hotend(self.config.extrude_temp)
        self.home()

    def send_gcode(self, command: str) -> str:
        self.logger.debug(f"Simulated command: {command}")
        if self.config.simulation['random_delay']['enabled']:
            time.sleep(random.uniform(
                self.config.simulation['random_delay']['min'],
                self.config.simulation['random_delay']['max']
            ))
        return "ok"

    def heat_hotend(self, target_temp: int) -> None:
        self.logger.info(f"Simulating heating to {target_temp}°C")
        while self.hotend_temp < target_temp:
            self.hotend_temp += random.uniform(20, 50)
            self.logger.debug(f"Current temperature: {self.hotend_temp:.1f}°C")
            time.sleep(1)
        self.logger.info("Target temperature reached")

    def home(self) -> None:
        self.logger.info("Simulating homing sequence")
        self.send_gcode("G28")
        self.x_pos = self.y_pos = self.z_pos = 0
        self.send_gcode("M83")


def create_printer(config_file: str) -> BasePrinter:
    with open(config_file, 'r') as f:
        config = json.load(f)

    printer_config = PrinterConfig(**config['printer'])

    if config['printer']['simulation']['enabled']:
        return SimulatedPrinter(printer_config)
    return RealPrinter(printer_config)