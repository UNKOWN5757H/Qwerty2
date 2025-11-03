# +++ Made By King [telegram username: @Shidoteshika1] +++

import os
import sys
import random
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from config import CUSTOM_CAPTION, OWNER_ID, PICS, BASE_URL
from database.database import kingdb
from helper_func import banUser, is_userJoin, is_admin, subscribed, encode, decode, get_messages
from plugins.autoDelete import auto_del_notification, delete_message
from plugins.FORMATS import START_MSG, FORCE_MSG
from plugins.premium import isprem
from plugins.short import get_shortlink


# ==========================================================================================
# /start command (handles both normal start and file retrieval)
# ==========================================================================================
@Bot.on_message(filters.command('start') & filters.private & ~banUser & subscribed)
async def start_command(client: Client, message: Message):
    await message.reply_chat_action(ChatAction.CHOOSE_STICKER)
    user_id = message.from_user.id

    # Add user to DB if not present
    if not await kingdb.present_user(user_id):
        try:
            await kingdb.add_user(user_id)
        except:
            pass

    text = message.text
    if len(text) <= 7:
        # Normal /start message
        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton('🤖 About me', callback_data='about'),
                InlineKeyboardButton('Settings ⚙️', callback_data='setting')
            ],
            [InlineKeyboardButton('💎 Get Premium', callback_data='premium')]
        ])
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup
        )
        try:
            await message.delete()
        except:
            pass
        return

    # Parameter detected (/start something)
    await message.delete()
    try:
        param = text.split(" ", 1)[1]
    except:
        return

    # Check if the link is new-style (date + random) or old base64
    if param[:8].isdigit():
        # ---------------- NEW DATE-BASED LINK ---------------- #
        file_data = await kingdb.get_link(param)
        if not file_data:
            return await message.reply("<b>⚠️ This link is invalid or expired!</b>", quote=True)

        first_id = file_data.get("first_msg_id")
        last_id = file_data.get("last_msg_id")

        try:
            await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
            ids = range(first_id, last_id + 1) if last_id else [first_id]
            messages = await get_messages(client, ids)
        except Exception as e:
            print(f"Error while fetching messages for code {param}: {e}")
            return await message.reply("<b><i>Something went wrong while retrieving files!</i></b>")

    else:
        # ---------------- OLD BASE64 LINK ---------------- #
        try:
            string = await decode(param)
            argument = string.split("-")
        except Exception as e:
            print(f"Decode failed for {param}: {e}")
            return

        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return
        else:
            return

        await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
        try:
            messages = await get_messages(client, ids)
        except:
            return await message.reply("<b><i>Something went wrong!</i></b>")

    # ---------------- Send Files ---------------- #
    AUTO_DEL, DEL_TIMER, HIDE_CAPTION, CHNL_BTN, PROTECT_MODE = await asyncio.gather(
        kingdb.get_auto_delete(),
        kingdb.get_del_timer(),
        kingdb.get_hide_caption(),
        kingdb.get_channel_button(),
        kingdb.get_protect_content()
    )

    button_name, button_link = (await kingdb.get_channel_button_link()) if CHNL_BTN else (None, None)

    last_message = None
    for idx, msg in enumerate(messages):
        if bool(CUSTOM_CAPTION) and bool(msg.document):
            caption = CUSTOM_CAPTION.format(
                previouscaption=msg.caption.html if msg.caption else "",
                filename=msg.document.file_name
            )
        elif HIDE_CAPTION and (msg.document or msg.audio):
            caption = ""
        else:
            caption = msg.caption.html if msg.caption else ""

        reply_markup = (
            InlineKeyboardMarkup([[InlineKeyboardButton(text=button_name, url=button_link)]])
            if CHNL_BTN and (msg.document or msg.photo or msg.video or msg.audio)
            else msg.reply_markup
        )

        try:
            copied = await msg.copy(
                chat_id=user_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                protect_content=PROTECT_MODE
            )
            await asyncio.sleep(0.1)
            if AUTO_DEL:
                asyncio.create_task(delete_message(copied, DEL_TIMER))
                if idx == len(messages) - 1:
                    last_message = copied
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue

    if AUTO_DEL and last_message:
        asyncio.create_task(auto_del_notification(client.username, last_message, DEL_TIMER, param))


# ==========================================================================================
# Force-Subscribe Handler (for unsubscribed users)
# ==========================================================================================
chat_data_cache = {}

@Bot.on_message(filters.command('start') & filters.private & ~banUser)
async def not_joined(client: Client, message: Message):
    temp = await message.reply("<b>🔍 Checking your subscription...</b>")
    user_id = message.from_user.id

    REQFSUB = await kingdb.get_request_forcesub()
    buttons = []
    count = 0

    try:
        channels = await kingdb.get_all_channels()
        for total, chat_id in enumerate(channels, start=1):
            await message.reply_chat_action(ChatAction.TYPING)

            if not await is_userJoin(client, user_id, chat_id):
                try:
                    # Cache chat data to reduce API calls
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    cname = data.title
                    if REQFSUB and not data.username:
                        link = await kingdb.get_stored_reqLink(chat_id)
                        await kingdb.add_reqChannel(chat_id)
                        if not link:
                            link = (await client.create_chat_invite_link(chat_id=chat_id, creates_join_request=True)).invite_link
                            await kingdb.store_reqLink(chat_id, link)
                    else:
                        link = data.invite_link

                    buttons.append([InlineKeyboardButton(text=cname, url=link)])
                    count += 1
                    await temp.edit(f"<b>Checking {count}/{total} channels...</b>")

                except Exception as e:
                    print(f"Force-sub error for {chat_id}: {e}")
                    return await temp.edit(
                        f"<b><i>⚠️ Error checking subscription. Contact developer @Sandalwood_Man</i></b>\n"
                        f"<blockquote>Reason: {e}</blockquote>"
                    )

        try:
            buttons.append([InlineKeyboardButton(text='♻️ Try Again', url=f"{BASE_URL}?start={message.command[1]}")])
        except IndexError:
            pass

        await temp.edit(
            text=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id,
                count=count,
                total=len(channels)
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        try:
            await message.delete()
        except:
            pass

    except Exception as e:
        print(f"Unable to perform force-sub: {e}")
        return await temp.edit(
            f"<b><i>⚠️ Error. Contact developer @Sandalwood_Man</i></b>\n<blockquote>Reason: {e}</blockquote>"
        )


# ==========================================================================================
# /restart Command (for Owner)
# ==========================================================================================
@Bot.on_message(filters.command('restart') & filters.private & filters.user(OWNER_ID))
async def restart_bot(client: Client, message: Message):
    print("Restarting bot...")
    msg = await message.reply("<b><i>⚙️ Restarting bot...</i></b>")
    try:
        await asyncio.sleep(6)
        await msg.delete()
        os.execl(sys.executable, sys.executable, "main.py")
    except Exception as e:
        print(f"Error during restart: {e}")
        await msg.edit_text(
            f"<b><i>⚠️ Error restarting bot. Contact developer @Sandalwood_Man</i></b>\n<blockquote>Reason: {e}</blockquote>"
        )
