# import os
# from twitchio.ext import commands
import serial
import time
from queue import Queue
# from threading import Thread
# import asyncio
# import json
import random

class Printer:
    XMAX = 200
    YMAX = 200
    ZMAX = 200

    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.serial = serial.Serial(port, baudrate, timeout=1)
        self.serial.flushInput()
        self.serial.flushOutput()
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0
        self.increment = 10  # Movement increment (in mm)
        self.extrude_amount = 2  # Extrusion amount (in mm of filament)
        self.feedrate = 1500  # Default feedrate (in mm/min)
        self.command_queue = Queue(maxsize=10)
        self.total_filament = 0
        self.running = True

    def send_gcode(self, command):
        print(f"Sending command: {command.strip()}")
        self.serial.write(command.encode())
        self.serial.flush()

        while True:
            response = self.serial.readline().decode().strip()
            if response:
                print(f"Printer response: {response}")
            if response[:2] == "ok":
                break

        return response

    def heat_hotend(self, target_temp=210):
        print(f"Heating hotend to {target_temp}C...")
        self.send_gcode(f"M104 S{target_temp}\n")
        while True:
            response = self.send_gcode("M105\n")
            if "T:" in response:
                current_temp = float(response.split("T:")[1].split(" ")[0])
                print(f"Current hotend temperature: {current_temp}C")
                if current_temp >= target_temp:
                    print("Hotend reached target temperature.")
                    break
            time.sleep(1)
        return response

    def home(self):
        print("Homing printer...")
        _ = self.send_gcode("G28\n")
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0

        # set printer extruder to relative mode
        # all other movements are absolute
        _ = self.send_gcode("M83\n")


    # TODO clean this up... should better combine this with process_command
    def move(self, x=None, y=None, z=None, extrude=False):
        command = f"G{'1' if extrude else '0'} "

        if x is not None:
            new_pos = max(0, min(self.XMAX, x))
            if not new_pos == self.x_pos:
                self.x_pos = new_pos
                command += f"X{self.x_pos} "
            else:
                command = None

        if y is not None:
            new_pos = max(0, min(self.YMAX, y))
            if not new_pos == self.y_pos:
                self.y_pos = new_pos
                command += f"Y{self.y_pos} "
            else:
                command = None

        if z is not None:
            new_pos = max(0, min(self.ZMAX, z))
            if not new_pos == self.z_pos:
                self.z_pos = new_pos
                command += f"Z{self.z_pos} "
            else:
                command = None

        if command is not None:
            if extrude:
                command += f"E{self.extrude_amount * 5} "
                self.total_filament -= self.extrude_amount

            command += f"F{self.feedrate}\n"
            self.send_gcode(command)

    def process_command(self, command, extrude=False):
        if command == 'back':
            self.move(y=self.y_pos + self.increment, extrude=extrude)
        elif command == 'forward':
            self.move(y=self.y_pos - self.increment, extrude=extrude)
        elif command == 'left':
            self.move(x=self.x_pos - self.increment, extrude=extrude)
        elif command == 'right':
            self.move(x=self.x_pos + self.increment, extrude=extrude)
        elif command == 'up':
            self.move(z=self.z_pos + self.increment, extrude=extrude)
        elif command == 'down':
            self.move(z=self.z_pos - self.increment, extrude=extrude)

    def run(self):
        while self.running:
            if not self.command_queue.empty():
                command = self.command_queue.get()

                # Check if there's a gift in the gift queue
                if self.total_filament >= self.extrude_amount:
                    print("Gift detected, extruding filament!")
                    # self.move(x=self.x_pos, y=self.y_pos, z=self.z_pos, extrude=True)
                    self.process_command(command, extrude=True)
                else:
                    self.process_command(command)

            time.sleep(0.1)  # Small delay to prevent busy-waiting

    def stop(self):
        self.running = False


class DummyPrinter:
    XMAX = 200
    YMAX = 200
    ZMAX = 200

    def __init__(self):
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0
        self.increment = 10  # Movement increment (in mm)
        self.extrude_amount = 2  # Extrusion amount (in mm of filament)
        self.feedrate = 1500  # Default feedrate (in mm/min)
        self.command_queue = Queue(maxsize=10)
        self.total_filament = 100
        self.running = True
        self.hotend_temp = 0

    def send_gcode(self, command):
        print(f"Dummy Printer received command: {command}")
        time.sleep(random.uniform(0.1, 0.5))  # Simulate command execution time
        return "ok"

    def heat_hotend(self, target_temp=210):
        print(f"Dummy Printer heating hotend to {target_temp}C...")
        while self.hotend_temp < target_temp:
            self.hotend_temp += random.uniform(10, 25)
            print(f"Current hotend temperature: {self.hotend_temp:.1f}C")
            time.sleep(1)
        print("Hotend reached target temperature.")

    def home(self):
        print("Homing printer...")
        _ = self.send_gcode("G28\n")
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0

        # set printer extruder to relative mode
        # all other movements are absolute
        _ = self.send_gcode("M83\n")

    def move(self, x=None, y=None, z=None, extrude=False):
        command = f"G{'1' if extrude else '0'} "

        if x is not None:
            new_pos = max(0, min(self.XMAX, x))
            if not new_pos == self.x_pos:
                self.x_pos = new_pos
                command += f"X{self.x_pos} "
            else:
                command = None

        if y is not None:
            new_pos = max(0, min(self.YMAX, y))
            if not new_pos == self.y_pos:
                self.y_pos = new_pos
                command += f"Y{self.y_pos} "
            else:
                command = None

        if z is not None:
            new_pos = max(0, min(self.ZMAX, z))
            if not new_pos == self.z_pos:
                self.z_pos = new_pos
                command += f"Z{self.z_pos} "
            else:
                command = None

        if command is not None:
            if extrude:
                command += f"E{self.extrude_amount * 5} "
                self.total_filament -= self.extrude_amount

            command += f"F{self.feedrate}\n"
            self.send_gcode(command)

    def process_command(self, command, extrude=False):
        if command == 'back':
            self.move(y=self.y_pos + self.increment, extrude=extrude)
        elif command == 'forward':
            self.move(y=self.y_pos - self.increment, extrude=extrude)
        elif command == 'left':
            self.move(x=self.x_pos - self.increment, extrude=extrude)
        elif command == 'right':
            self.move(x=self.x_pos + self.increment, extrude=extrude)
        elif command == 'up':
            self.move(z=self.z_pos + self.increment, extrude=extrude)
        elif command == 'down':
            self.move(z=self.z_pos - self.increment, extrude=extrude)

    def run(self):
        while self.running:
            if not self.command_queue.empty():
                command = self.command_queue.get()

                # Check if there's a gift in the gift queue
                if self.total_filament >= self.extrude_amount:
                    print("Gift detected, extruding filament!")
                    # self.move(x=self.x_pos, y=self.y_pos, z=self.z_pos, extrude=True)
                    self.process_command(command, extrude=True)
                else:
                    print("print moving!")
                    self.process_command(command)

            time.sleep(1)  # Small delay to prevent busy-waiting

    def stop(self):
        self.running = False
