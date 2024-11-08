import json
from TikTokLive import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent
import asyncio
from threading import Thread
import logging

from printer_control import create_printer

with open("config.json", "r") as f:
    config = json.load(f)

logging.basicConfig(
    level=getattr(logging, config['logging']['level']),
    format=config['logging']['format'],
    filename=config['logging']['file']
)

printer = create_printer("config.json")
printer.setup_printer()

client = TikTokLiveClient(unique_id=config['tiktok']['unique_id'])
client.logger.setLevel(LogLevel.INFO.value)

@client.on(ConnectEvent)
async def on_connect(event):
    printer.logger.info(f"Connected to @{event.unique_id} (Room ID: {client.room_id})")

@client.on(CommentEvent)
async def on_comment(event):
    comment = event.comment.split(" ")[0].lower()
    if comment in ['back', 'forward', 'left', 'right', 'up', 'down']:
        printer.command_queue.put(comment)
        printer.logger.info(f"{event.user.nickname} -> {event.comment}")

@client.on(GiftEvent)
async def on_gift(event):
    if not event.gift.streakable or not event.streaking:
        gift_count = event.repeat_count or 1
        total_gift_coins = gift_count * event.gift.diamond_count
        printer.total_filament += total_gift_coins
        printer.logger.info(f"Received {event.gift.name} worth {total_gift_coins} coins. Total: {printer.total_filament}")


if __name__ == '__main__':
    printer_thread = Thread(target=printer.run)
    printer_thread.start()

    try:
        client.run()
    except KeyboardInterrupt:
        print("Stopping program...")
    finally:
        printer.stop()
        printer_thread.join()
