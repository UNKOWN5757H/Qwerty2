# +++ Made By King [telegram username: @Shidoteshika1] +++

import asyncio
import secrets
import string
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from config import BASE_URL
from database.database import kingdb
from helper_func import get_message_id, is_admin


# ==========================================================
# Utility: Generate unique date-based code
# Example: 20251103Ab9XkLp2
# ==========================================================
def generate_code(length: int = 8) -> str:
    date_prefix = datetime.now().strftime("%Y%m%d")
    random_suffix = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    return f"{date_prefix}{random_suffix}"


# ==========================================================
# /batch — Create multi-file link
# ==========================================================
@Bot.on_message(filters.command("batch") & filters.private & is_admin)
async def batch(client: Client, message: Message):
    channel = f"<a href={client.db_channel.invite_link}>ᴅʙ ᴄʜᴀɴɴᴇʟ</a>"

    # Ask for first message
    while True:
        try:
            first_message = await client.ask(
                text=(f"<b><blockquote>Fᴏʀᴡᴀʀᴅ ᴛʜᴇ Fɪʀsᴛ Mᴇssᴀɢᴇ ғʀᴏᴍ {channel}</blockquote>\n"
                      f"<blockquote>Oʀ sᴇɴᴅ ᴛʜᴇ {channel} ᴘᴏsᴛ ʟɪɴᴋ</blockquote></b>"),
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
                disable_web_page_preview=True,
            )
        except:
            return

        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        await first_message.reply(
            f"<b>❌ Eʀʀᴏʀ..\n<blockquote>Tʜɪs Fᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ {channel}</blockquote></b>",
            quote=True
        )

    # Ask for last message
    while True:
        try:
            second_message = await client.ask(
                text=(f"<b><blockquote>Fᴏʀᴡᴀʀᴅ ᴛʜᴇ Lᴀsᴛ Mᴇssᴀɢᴇ ғʀᴏᴍ {channel}</blockquote>\n"
                      f"<blockquote>Oʀ sᴇɴᴅ ᴛʜᴇ {channel} ᴘᴏsᴛ ʟɪɴᴋ</blockquote></b>"),
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
                disable_web_page_preview=True,
            )
        except:
            return

        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        await second_message.reply(
            f"<b>❌ Eʀʀᴏʀ..\n<blockquote>Tʜɪs Fᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ {channel}</blockquote></b>",
            quote=True
        )

    # Generate and store new-style link
    code = generate_code()
    await kingdb.save_link(code, f_msg_id, s_msg_id)

    link = f"{BASE_URL}?start={code}"
    share_url = f"https://telegram.me/share/url?url={link}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Sʜᴀʀᴇ URL", url=share_url)]])
    await second_message.reply_text(
        f"<b>✅ Bᴇʟᴏᴡ ɪs ʏᴏᴜʀ ʙᴀᴛᴄʜ ʟɪɴᴋ:</b>\n<blockquote>{link}</blockquote>",
        quote=True,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )


# ==========================================================
# /genlink — Create single-file link
# ==========================================================
@Bot.on_message(filters.command("genlink") & filters.private & is_admin)
async def link_generator(client: Client, message: Message):
    channel = f"<a href={client.db_channel.invite_link}>ᴅʙ ᴄʜᴀɴɴᴇʟ</a>"

    while True:
        try:
            channel_message = await client.ask(
                text=(f"<b><blockquote>Fᴏʀᴡᴀʀᴅ ᴛʜᴇ Mᴇssᴀɢᴇ ғʀᴏᴍ {channel}</blockquote>\n"
                      f"<blockquote>Oʀ sᴇɴᴅ ᴛʜᴇ {channel} ᴘᴏsᴛ ʟɪɴᴋ</blockquote></b>"),
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
                disable_web_page_preview=True,
            )
        except:
            return

        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        await channel_message.reply(
            f"<b>❌ Eʀʀᴏʀ..\n<blockquote>Tʜɪs Fᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ {channel}</blockquote></b>",
            quote=True
        )

    # Generate and store single message link
    code = generate_code()
    await kingdb.save_link(code, msg_id, msg_id)

    link = f"{BASE_URL}?start={code}"
    share_url = f"https://telegram.me/share/url?url={link}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Sʜᴀʀᴇ URL", url=share_url)]])
    await channel_message.reply_text(
        f"<b>✅ Bᴇʟᴏᴡ ɪs ʏᴏᴜʀ ʟɪɴᴋ:</b>\n<blockquote>{link}</blockquote>",
        quote=True,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )
