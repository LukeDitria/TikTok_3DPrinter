import json
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent
import asyncio
from threading import Thread
import os

from printer_control import create_printer

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(os.path.dirname(script_dir), "config.json")

with open(config_path, "r") as f:
    config = json.load(f)

printer = create_printer(config_path)
client = TikTokLiveClient(unique_id=config['tiktok']['unique_id'])

@client.on(ConnectEvent)
async def on_connect(event):
    print(f"Connected to @{event.unique_id} (Room ID: {client.room_id})")

@client.on(CommentEvent)
async def on_comment(event):
    comment = event.comment.split(" ")[0].lower()
    if comment in ['back', 'forward', 'left', 'right', 'up', 'down']:
        printer.command_queue.put(comment)
        print(f"{event.user.nickname} -> {event.comment}")

@client.on(GiftEvent)
async def on_gift(event):
    if not event.gift.streakable or not event.streaking:
        gift_count = event.repeat_count or 1
        total_gift_coins = gift_count * event.gift.diamond_count
        printer.total_filament += total_gift_coins
        print(f"Received {event.gift.name} worth {total_gift_coins} coins. Total: {printer.total_filament}")

async def run_client():
    while True:
        try:
            await client.start()
        except Exception as e:
            print(f"Connection error: {e}, reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == '__main__':
    printer_thread = Thread(target=printer.run)
    printer_thread.start()

    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        print("Stopping program...")
    finally:
        printer.stop()
        printer_thread.join()
