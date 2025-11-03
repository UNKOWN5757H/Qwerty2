# +++ Made By King [telegram username: @Sandalwood_Man] +++

import asyncio
import sys
from aiohttp import web
from datetime import datetime
from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode
import pyromod.listen

from plugins import web_server
from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, CHANNEL_ID, PORT, OWNER_ID, BASE_URL 


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        bot_info = await self.get_me()
        self.name = bot_info.first_name
        self.username = bot_info.username
        self.uptime = datetime.now()

        try:
            db_channel = await self.get_chat(CHANNEL_ID)

            if not db_channel.invite_link:
                db_channel.invite_link = await self.export_chat_invite_link(CHANNEL_ID)

            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Testing")
            await test.delete()

        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(
                f"Make sure the bot is Admin in DB Channel and has proper Permissions. Current Value: {CHANNEL_ID}"
            )
            self.LOGGER(__name__).info("Bot stopped.")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Advanced File-Sharing Bot V3")
        self.LOGGER(__name__).info(f"{self.name} Bot Running..!")
        self.LOGGER(__name__).info(f"OPERATION SUCCESSFUL ✅")

        # Start premium cleanup background task
        from plugins.premium import check_and_clean_premium_users
        asyncio.create_task(check_and_clean_premium_users())

        # Start web server
        runner = web.AppRunner(await web_server())
        await runner.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(runner, bind_address, PORT).start()

        # Notify owner
        try:
            await self.send_message(OWNER_ID, text="<b><blockquote>🤖 Bot Restarted ♻️</blockquote></b>")
        except:
            pass

        # Keep bot + web server alive
        await idle()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info(f"{self.name} Bot stopped.")
