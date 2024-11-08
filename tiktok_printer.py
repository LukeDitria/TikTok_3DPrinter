import json
import logging
import asyncio
from threading import Thread
from typing import Optional
from dataclasses import dataclass
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent
from printer_control import create_printer


@dataclass
class TikTokConfig:
    unique_id: str
    reconnect_delay: int
    commands: dict


class TikTokPrinterController:
    def __init__(self, config_file: str):
        self.setup_logging(config_file)
        self.load_config(config_file)
        self.printer = create_printer(config_file)
        self.client = TikTokLiveClient(unique_id=self.tiktok_config.unique_id)
        self.setup_event_handlers()

    def setup_logging(self, config_file: str):
        with open(config_file, 'r') as f:
            config = json.load(f)

        logging.basicConfig(
            level=getattr(logging, config['logging']['level']),
            format=config['logging']['format'],
            filename=config['logging']['file']
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self, config_file: str):
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.tiktok_config = TikTokConfig(**config['tiktok'])

    def setup_event_handlers(self):
        @self.client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            self.logger.info(f"Connected to @{event.unique_id} (Room ID: {self.client.room_id})")

        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            comment = event.comment.split(" ")[0].lower()
            if comment in self.tiktok_config.commands['movement']:
                self.logger.info(f"Movement command from {event.user.nickname}: {comment}")
                self.printer.command_queue.put(comment)

        @self.client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            if not event.gift.streakable or not event.streaking:
                gift_count = event.repeat_count or 1
                total_gift_coins = (
                        gift_count *
                        event.gift.diamond_count *
                        self.tiktok_config.commands['gift_to_filament_ratio']
                )
                self.printer.total_filament += total_gift_coins
                self.logger.info(
                    f"Gift received: {event.gift.name} worth {total_gift_coins} "
                    f"filament units. Total: {self.printer.total_filament}"
                )

    async def run_client(self):
        while True:
            try:
                await self.client.start()
            except Exception as e:
                self.logger.error(f"TikTok connection error: {e}")
                self.logger.info(f"Reconnecting in {self.tiktok_config.reconnect_delay} seconds...")
                await asyncio.sleep(self.tiktok_config.reconnect_delay)

    def start(self):
        self.printer_thread = Thread(target=self.printer.run)
        self.printer_thread.start()

        try:
            asyncio.run(self.run_client())
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            self.stop()

    def stop(self):
        self.logger.info("Shutting down TikTok Printer Controller")
        self.printer.stop()
        self.printer_thread.join()


if __name__ == '__main__':
    controller = TikTokPrinterController("config.json")
    controller.start()