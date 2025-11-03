# bot/premium.py

import asyncio
import re
from datetime import datetime, timedelta
from bot import Bot
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import OWNER_ID
from database.database import kingdb


async def get_variable(key, default=None):
    """Get variable from database"""
    return await kingdb.get_variable(key, default)


async def set_variable(key, value):
    """Set or update variable in database"""
    await kingdb.set_variable(key, value)


def parse_duration(duration_str):
    """
    Parses a duration string like '1d 2h 30m 45s' or '5d' and returns a timedelta.
    """
    matches = re.findall(r"(\d+)\s*([dhms])", duration_str.lower())
    if not matches:
        raise ValueError("Invalid duration format")
    delta = timedelta()
    for value, unit in matches:
        value = int(value)
        if unit == "d":
            delta += timedelta(days=value)
        elif unit == "h":
            delta += timedelta(hours=value)
        elif unit == "m":
            delta += timedelta(minutes=value)
        elif unit == "s":
            delta += timedelta(seconds=value)
    return delta

@Bot.on_message(filters.command("addpremium") & filters.user(OWNER_ID) & filters.private)
async def add_premium(client, message: Message):
    """Add premium access to a user"""
    args = message.text.split(maxsplit=2)
    user_id = None
    time_text = None

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        if len(args) > 1:
            time_text = args[1]
    elif len(args) == 3:
        try:
            user_id = int(args[1])
            time_text = args[2]
        except ValueError:
            await message.reply(
                "❓ Invalid user ID. Use `/addpremium <user_id> <time>` or reply to a user.",
                quote=True,
            )
            return

    if not user_id:
        await message.reply(
            "❓ Please reply to a user or use `/addpremium <user_id> <time>`.\n\n"
            "🕒 <b>Examples:</b> <code>1d</code> <code>2h</code> <code>30m</code>",
            quote=True,
        )
        return

    while not time_text:
        ask_msg = await message.reply(
            "💎 <b>Set Premium Duration</b>\n\n"
            "🕒 <b>Examples:</b> <code>1d</code> <code>2h</code> <code>30m</code> <code>45s</code>\n"
            "🔤 <b>Format:</b> <code>[number][d/h/m/s]</code>\n"
            "  <b>d</b> = days | <b>h</b> = hours | <b>m</b> = minutes | <b>s</b> = seconds\n\n"
            "❌ Type <code>cancel</code> to abort.",
            quote=True,
        )
        try:
            resp = await client.listen(
                chat_id=message.chat.id, user_id=message.from_user.id, timeout=30
            )
        except Exception:
            await ask_msg.edit(
                "⌛ <b>Timeout!</b> Operation <b>cancelled</b>.\n\n🔁 Please try again."
            )
            return
        if resp.text.lower() in ["cancel", "❌"]:
            await ask_msg.edit("❌ Cancelled.")
            return
        time_text = resp.text.strip()

    try:
        expires_in = parse_duration(time_text)
    except ValueError:
        await message.reply(
            "⚠️ <b>Invalid time format!</b>\n"
            "📝 <b>Examples:</b> <code>1d</code> <code>2h 30m</code> <code>1d 5m 25s</code>\n"
            "  <b>d</b> = days | <b>h</b> = hours | <b>m</b> = minutes | <b>s</b> = seconds",
            quote=True,
        )
        return

    if expires_in.total_seconds() == 0:
        await message.reply(
            "⚠️ <b>Duration must be greater than zero!</b>",
            quote=True,
        )
        return

    expires_at = datetime.now() + expires_in
    expires_iso = expires_at.isoformat()

    pusers = await get_variable("puser") or {}
    existed = str(user_id) in pusers

    pusers[str(user_id)] = expires_iso
    await set_variable("puser", pusers)

    action = "🔁 Updated" if existed else "✅ Added"
    await message.reply(
        f"{action} premium for `{user_id}` until `{expires_at.strftime('%Y-%m-%d %H:%M:%S')}`",
        quote=True,
    )

@Bot.on_message(filters.command("rempremium") & filters.user(OWNER_ID) & filters.private)
async def remove_premium(client, message: Message):
    """Remove premium access from a user"""
    args = message.text.split(maxsplit=1)
    user_id = None

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(args) == 2:
        try:
            user_id = int(args[1])
        except ValueError:
            await message.reply("❓ Invalid user ID. Please provide a valid numeric ID.", quote=True)
            return
    else:
        await message.reply(
            "❓ Please reply to a user or use `/rempremium <user_id>`.", quote=True
        )
        return

    pusers = await get_variable("puser") or {}

    if str(user_id) not in pusers:
        await message.reply("⚠️ This user is not in the premium list.", quote=True)
        return

    pusers.pop(str(user_id))
    await set_variable("puser", pusers)

    await message.reply(f"❌ Removed premium access for `{user_id}`", quote=True)


async def check_and_clean_premium_users():
    """Background task to clean expired premium users"""
    while True:
        try:
            pusers = await get_variable("puser") or {}
            updated_pusers = {}

            now = datetime.now()
            for user_id, exp_date_str in pusers.items():
                try:
                    exp_date = datetime.fromisoformat(exp_date_str)
                    if exp_date > now:
                        updated_pusers[user_id] = exp_date_str
                except Exception as e:
                    print(f"Error parsing date for user {user_id}: {e}")
                    continue

            if updated_pusers != pusers:
                await set_variable("puser", updated_pusers)

        except Exception as e:
            print(f"Error in premium check loop: {e}")

        await asyncio.sleep(600)  # Check every 10 minutes

@Bot.on_message(filters.command("premiumlist") & filters.user(OWNER_ID) & filters.private)
async def list_premium_users(client, message: Message):
    """List all premium users with expiry info"""
    pusers = await get_variable("puser") or {}

    if not pusers:
        await message.reply("❌ No premium users found.", quote=True)
        return

    now = datetime.now()
    lines = []
    count = 1

    for uid, exp_str in pusers.items():
        try:
            exp_time = datetime.fromisoformat(exp_str)
            remaining = exp_time - now

            if remaining.total_seconds() <= 0:
                continue

            if remaining.days > 0:
                time_left = f"{remaining.days}d {remaining.seconds // 3600}h"
            elif remaining.seconds > 3600:
                time_left = (
                    f"{remaining.seconds // 3600}h {(remaining.seconds % 3600) // 60}m"
                )
            elif remaining.seconds > 60:
                time_left = f"{remaining.seconds // 60}m"
            else:
                time_left = f"{remaining.seconds}s"

            try:
                user = await client.get_users(int(uid))
                user_mention = f"<a href='tg://user?id={uid}'>👤 {user.first_name}</a>"
            except (PeerIdInvalid, Exception):
                user_mention = "❓ Unknown User"

            lines.append(
                f"{count}. {user_mention} | 🆔 <code>{uid}</code>\n"
                f"    ⏳ Expires: <code>{exp_time.strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
                f"    🕒 Time Left: <b>{time_left}</b>"
            )
            count += 1

        except Exception as e:
            print(f"Error parsing {uid}: {e}")
            continue

    if not lines:
        await message.reply("❌ No valid premium users found.", quote=True)
        return

    text = "💎 <b>Premium Users List</b> 💎\n\n" + "\n\n".join(lines)
    await message.reply(text, quote=True, disable_web_page_preview=True)


async def premcall(client, query: CallbackQuery):
    """Handle premium callback query"""
    text = (
        "<u>𝗔𝗻𝗶𝗺𝗲𝗧𝗼𝗼𝗻 𝗜𝗡𝗗𝗘𝗫 </u>🌟\n\n"
        "<blockquote expandable><b>ʙᴇɴᴇꜰɪᴛꜱ ᴏꜰ ᴩʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ :-</b>\n\n"
        "🌸 ʏᴏᴜ ᴄᴀɴ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ɢᴇᴛ 🌐 ᴀʟʟ ᴀɴɪᴍᴇ ᴇᴩɪꜱᴏᴅᴇꜱ ꜰʀᴇᴇ ( ɴᴏ ᴀᴅꜱ )</blockquote>\n\n"
        "<blockquote expandable><b>ᴀɴɪᴍᴇᴛᴏᴏɴ ᴩʀᴇᴍɪᴜᴍ ᴩʟᴀɴꜱ ⚜️</b>\n\n"
        "⚡ ᴍᴏɴᴛʜʟʏ - 40₹  \n"
        "⭐ 6 ᴍᴏɴᴛʜꜱ - 199₹  \n"
        "🌟 12 ᴍᴏɴᴛʜꜱ - 399₹</blockquote>\n\n"
        "💳 𝐔𝐏𝐈 / 𝐁𝐚𝐧𝐤 𝐓𝐫𝐚𝐧𝐬𝐟𝐞𝐫 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞  \n\n"
        f"⚜️ 𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐅𝐨𝐫 <b>@JD_Namikaze</b>  \n"
        "𝐁𝐮𝐲 𝐘𝐨𝐮𝐫 𝐏𝐫𝐞𝐦𝐢𝐮𝐦 🌟"
    )
    
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Buy Premium",
                    url=f"tg://user?id={OWNER_ID}"
                ),
                InlineKeyboardButton(
                    text="🎇 Cancel",
                    callback_data="close"
                ),
            ]
        ]
    )
    
    await query.message.edit_text(
        text=text,
        reply_markup=reply_markup,
    )


async def isprem(uid):
    """Check if user is premium"""
    pusers = await get_variable("puser", {})
    now = datetime.now()
    
    if str(uid) in pusers:
        try:
            exp_date = datetime.fromisoformat(pusers[str(uid)])
            if exp_date > now:
                return True
        except Exception:
            pass
    return False


