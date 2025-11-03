# +++ Made By King [telegram username: @Shidoteshika1] +++
# ============================================================
# LINK GENERATOR PLUGIN
# Generates short, date-based unique download links
# Compatible with SidDataBase (kingdb) from database.py
# ============================================================

import secrets
import string
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import BASE_URL
from helper_func import get_message_id, is_admin
from database import database


# ============================================================
# 🔤 RANDOM CODE GENERATOR
# ============================================================
def generate_unique_code():
    today_str = datetime.utcnow().strftime("%Y%m%d")
    rand_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    return f"{today_str}{rand_part}"


# ============================================================
# 🎯 BATCH LINK GENERATOR
# ============================================================
@Bot.on_message(filters.command('batch') & filters.private & is_admin)
async def batch(client: Client, message: Message):
    channel = f"<a href={client.db_channel.invite_link}>ᴅʙ ᴄʜᴀɴɴᴇʟ</a>"

    # First message
    while True:
        try:
            first_message = await client.ask(
                text=(
                    f"<b><blockquote>Fᴏʀᴡᴀʀᴅ ᴛʜᴇ Fɪʀsᴛ Mᴇssᴀɢᴇ ғʀᴏᴍ {channel} (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..</blockquote>\n"
                    f"<blockquote>Oʀ Sᴇɴᴅ ᴛʜᴇ {channel} Pᴏsᴛ Lɪɴᴋ</blockquote></b>"
                ),
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=120,
                disable_web_page_preview=True
            )
        except:
            return

        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        await first_message.reply(
            f"<b>❌ Eʀʀᴏʀ..\n<blockquote>Tʜɪs ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ {channel}</blockquote></b>",
            quote=True
        )

    # Second message
    while True:
        try:
            second_message = await client.ask(
                text=(
                    f"<b><blockquote>Fᴏʀᴡᴀʀᴅ ᴛʜᴇ Lᴀsᴛ Mᴇssᴀɢᴇ ғʀᴏᴍ {channel} (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..</blockquote>\n"
                    f"<blockquote>Oʀ Sᴇɴᴅ ᴛʜᴇ {channel} Pᴏsᴛ Lɪɴᴋ</blockquote></b>"
                ),
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=120,
                disable_web_page_preview=True
            )
        except:
            return

        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        await second_message.reply(
            f"<b>❌ Eʀʀᴏʀ..\n<blockquote>Tʜɪs ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ {channel}</blockquote></b>",
            quote=True
        )

    # Generate and save link
    unique_code = generate_unique_code()
    await kingdb.save_link(unique_code, f_msg_id, s_msg_id)

    link = f"{BASE_URL}?start={unique_code}"
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔁 Sʜᴀʀᴇ URL", url=f'https://telegram.me/share/url?url={link}')]]
    )

    await second_message.reply_text(
        f"<b>✅ Yᴏᴜʀ Bᴀᴛᴄʜ Lɪɴᴋ ɪs Rᴇᴀᴅʏ!</b>\n<blockquote>{link}</blockquote>",
        quote=True,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


# ============================================================
# 🎯 SINGLE MESSAGE LINK GENERATOR
# ============================================================
@Bot.on_message(filters.command('genlink') & filters.private & is_admin)
async def genlink(client: Client, message: Message):
    channel = f"<a href={client.db_channel.invite_link}>ᴅʙ ᴄʜᴀɴɴᴇʟ</a>"

    while True:
        try:
            channel_message = await client.ask(
                text=(
                    f"<b><blockquote>Fᴏʀᴡᴀʀᴅ ᴛʜᴇ Mᴇssᴀɢᴇ ғʀᴏᴍ {channel} (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..</blockquote>\n"
                    f"<blockquote>Oʀ Sᴇɴᴅ ᴛʜᴇ {channel} Pᴏsᴛ Lɪɴᴋ</blockquote></b>"
                ),
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=120,
                disable_web_page_preview=True
            )
        except:
            return

        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        await channel_message.reply(
            f"<b>❌ Eʀʀᴏʀ..\n<blockquote>Tʜɪs ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ {channel}</blockquote></b>",
            quote=True
        )

    # Generate and save single link
    unique_code = generate_unique_code()
    await kingdb.save_link(unique_code, msg_id)

    link = f"{BASE_URL}?start={unique_code}"
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔁 Sʜᴀʀᴇ URL", url=f'https://telegram.me/share/url?url={link}')]]
    )

    await channel_message.reply_text(
        f"<b>✅ Yᴏᴜʀ Lɪɴᴋ ɪs Rᴇᴀᴅʏ!</b>\n<blockquote>{link}</blockquote>",
        quote=True,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
