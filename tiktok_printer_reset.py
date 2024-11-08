from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent
import serial
import time
import asyncio
from queue import Queue
from threading import Thread


class Printer:
    XMAX = 200
    YMAX = 200
    ZMAX = 200

    def __init__(self, baudrate=115200):
        try:
            port = '/dev/ttyUSB0'
            self.serial = serial.Serial(port, baudrate, timeout=1)
        except Exception as e:
            print(f"Failed to connect: {e}")

        try:
            port = '/dev/ttyUSB1'
            self.serial = serial.Serial(port, baudrate, timeout=1)
        except Exception as e:
            print(f"Failed to connect: {e}")

        print(f"connected to {port}")
        self.serial.flushInput()
        self.serial.flushOutput()
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0
        self.increment = 10  # Movement increment (in mm)
        self.extrude_amount = 1  # Extrusion amount (in mm of filament)
        self.feedrate = 1500  # Default feedrate (in mm/min)
        self.command_queue = Queue(maxsize=20)
        self.total_coins = 0
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

    def home(self):
        print("Homing printer...")
        _ = self.send_gcode("G28\n")
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0

        # set printer extruder to relative mode
        # all other movements are absolute
        _ = self.send_gcode("M83\n")
        # self.update_position()  # Update position before each move

    def move(self, x=None, y=None, z=None, extrude=False):
        # self.update_position()  # Update position before each move

        command = f"G{'1' if extrude else '0'} "

        if x is not None:
            new_pos = max(0.2, min(self.XMAX, x))
            if not new_pos == self.x_pos:
                self.x_pos = new_pos
                command += f"X{self.x_pos} "
            else:
                command = None

        if y is not None:
            new_pos = max(0.2, min(self.YMAX, y))
            if not new_pos == self.y_pos:
                self.y_pos = new_pos
                command += f"Y{self.y_pos} "
            else:
                command = None

        if z is not None:
            new_pos = max(0.2, min(self.ZMAX, z))
            if not new_pos == self.z_pos:
                self.z_pos = new_pos
                command += f"Z{self.z_pos} "
            else:
                command = None

        if command is not None:
            if extrude:
                command += f"E{self.extrude_amount * 5} "
                self.total_coins -= self.extrude_amount

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

    def update_position(self):
        """Fetch the current real-time position from the printer."""
        response = self.send_gcode("M114\n")
        # Parse the response, typically in the format: "X:0.00 Y:127.00 Z:145.00 E:0.00"
        if "X:" in response and "Y:" in response and "Z:" in response:
            try:
                parts = response.split()
                self.x_pos = float(parts[0].split(":")[1])
                self.y_pos = float(parts[1].split(":")[1])
                self.z_pos = float(parts[2].split(":")[1])
                print(f"Updated real position - X: {self.x_pos}, Y: {self.y_pos}, Z: {self.z_pos}")
            except Exception as e:
                print(f"Failed to update position: {e}")

    def run(self):
        while self.running:
            if not self.command_queue.empty():
                command = self.command_queue.get()
                # self.process_command(command, extrude=True)

                # Check if there's a gift in the gift queue
                if self.total_coins >= self.extrude_amount:
                    print("Gift detected, extruding filament!")
                    # self.move(x=self.x_pos, y=self.y_pos, z=self.z_pos, extrude=True)
                    self.process_command(command, extrude=True)
                else:
                    self.process_command(command)

                time.sleep(1)  # Small delay to prevent busy-waiting

    def stop(self):
        self.running = False


# Create the printer instance
printer = Printer()

# Create the TikTok client
client: TikTokLiveClient = TikTokLiveClient(unique_id="@lukeditria")
# client: TikTokLiveClient = TikTokLiveClient(unique_id="@sammiedojaking")


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"Connected to @{event.unique_id} (Room ID: {client.room_id})")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    comment = event.comment.split(" ")[0].lower()
    if comment in ['back', 'forward', 'left', 'right', 'up', 'down']:
        printer.command_queue.put(comment)
        print(f"{event.user.nickname} -> {event.comment}")
    if comment == "home" and event.user.unique_id =="lukeditria":
        printer.home()
    	

@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    if event.gift.streakable and event.streaking:
        return

    else:
        gift_count = event.repeat_count or 1
        gift_name = event.gift.name
        total_gift_coins = gift_count * event.gift.diamond_count
        printer.total_coins += total_gift_coins  # Add coins to the total
        print(f"Received {gift_name} worth {total_gift_coins} coins. Total coins: {printer.total_coins}")


def setup_printer():
    printer.heat_hotend(240)  # Heat to 210°C
    printer.home()
    printer.move(x=100, y=100, z=50, extrude=False)

async def run_client():
    while True:
        try:
            await client.start()
        except Exception as e:
            print(f"Connection error: {e}")
            print("Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)
        else:
            # If we reach here, it means the client.start() completed without error
            # This could happen if the stream ended normally
            print("Stream ended. Waiting before attempting to reconnect...")
            await asyncio.sleep(5)

if __name__ == '__main__':
    setup_printer()

    # Start the printer processing thread
    printer_thread = Thread(target=printer.run)
    printer_thread.start()

    try:
        # Run the TikTok client with reconnection attempts
        asyncio.run(run_client())
    except KeyboardInterrupt:
        print("Stopping the program...")
    finally:
        # Stop the printer thread
        printer.stop()
        printer_thread.join()

        # Ensure the client is stopped
        asyncio.run(client.stop())

    printer.heat_hotend(0)
    print("Program ended.")
