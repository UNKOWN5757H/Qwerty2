# +++ Made By King [telegram username: @Shidoteshika1] +++

import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import OWNER_ID
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait
from database.database import kingdb 

#=============================================================================================================================================================================
# -------------------- HELPER FUNCTIONS FOR USER VERIFICATION IN DIFFERENT CASES -------------------- 
#=============================================================================================================================================================================

# used for checking banned user
async def check_banUser(filter, client, update):
    try:
        user_id = update.from_user.id
        return await kingdb.ban_user_exist(user_id)
    except: #Exception as e:
        #print(f"!Error on check_banUser(): {e}")
        return False


#used for cheking if a user is admin ~Owner also treated as admin level
async def check_admin(filter, client, update):
    try:
        user_id = update.from_user.id       
        return any([user_id == OWNER_ID, await kingdb.admin_exist(user_id)])
    except Exception as e:
        print(f"! Exception in check_admin: {e}")
        return False


# Check user subscription in Channels in a more optimized way
async def is_subscribed(filter, client, update):
    Channel_ids = await kingdb.get_all_channels()
    
    if not Channel_ids:
        return True

    user_id = update.from_user.id

    if any([user_id == OWNER_ID, await kingdb.admin_exist(user_id)]):
        return True

    # Handle the case for a single channel directly (no need for gather)
    if len(Channel_ids) == 1:
        return await is_userJoin(client, user_id, Channel_ids[0])

    # Use asyncio gather to check multiple channels concurrently
    tasks = [is_userJoin(client, user_id, ids) for ids in Channel_ids if ids]
    results = await asyncio.gather(*tasks)

    # If any result is False, return False; else return True
    return all(results)


#Chcek user subscription by specifying channel id and user id
async def is_userJoin(client, user_id, channel_id):
    #REQFSUB = await kingdb.get_request_forcesub()
    try:
        member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER}
        
    except UserNotParticipant:
        if await kingdb.get_request_forcesub(): #and await privateChannel(client, channel_id):
                return await kingdb.reqSent_user_exist(channel_id, user_id)
            
        return False
        
    except Exception as e:
        print(f"!Error on is_userJoin(): {e}")
        return False
#=============================================================================================================================================================================
#=============================================================================================================================================================================
    
async def encode(string):
    try:
        string_bytes = string.encode("ascii")
        base64_bytes = base64.urlsafe_b64encode(string_bytes)
        base64_string = (base64_bytes.decode("ascii")).strip("=")
        return base64_string
    except Exception as e:
        print(f'Error occured on encode, reason: {e}')

async def decode(base64_string):
    try:
        base64_string = base64_string.strip("=") # links generated before this commit will be having = sign, hence striping them to handle padding errors.
        base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
        string_bytes = base64.urlsafe_b64decode(base64_bytes) 
        string = string_bytes.decode("ascii")
        return string
    except Exception as e:
        print(f'Error occured on decode, reason: {e}')

async def get_messages(client, message_ids):
    try:
        messages = []
        total_messages = 0
        while total_messages != len(message_ids):
            temb_ids = message_ids[total_messages:total_messages+200]
            try:
                msgs = await client.get_messages(
                    chat_id=client.db_channel.id,
                    message_ids=temb_ids
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                msgs = await client.get_messages(
                    chat_id=client.db_channel.id,
                    message_ids=temb_ids
                )
            except:
                pass
            total_messages += len(temb_ids)
            messages.extend(msgs)
        return messages
    except Exception as e:
        print(f'Error occured on get_messages, reason: {e}')

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern,message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0


def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Check user subscription in Channels
"""async def is_subscribed(filter, client, update):
    Channel_ids = await kingdb.get_all_channels()
    
    if not Channel_ids:
        return True

    user_id = update.from_user.id

    if any([user_id == OWNER_ID, await kingdb.admin_exist(user_id)]):
        return True
        
    member_status = ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER
    
    REQFSUB = await kingdb.get_request_forcesub()
                    
    for id in Channel_ids:
        if not id:
            continue
            
        try:
            member = await client.get_chat_member(chat_id=id, user_id=user_id)
        except UserNotParticipant:
            member = None
            if REQFSUB and await privateChannel(client, id):
                if not await kingdb.reqSent_user_exist(id, user_id):
                    return False
            else:
                return False
                
        if member:
            if member.status not in member_status:
                if REQFSUB and await privateChannel(client, id):
                    if not await kingdb.reqSent_user_exist(id, user_id):
                        return False
                else:
                    return False

    return True"""

#Check user subscription in Channels in More Simpler way
"""async def is_subscribed(filter, client, update):
    Channel_ids = await kingdb.get_all_channels()
    
    if not Channel_ids:
        return True

    user_id = update.from_user.id

    if any([user_id == OWNER_ID, await kingdb.admin_exist(user_id)]):
        return True

    for ids in Channel_ids:
        if not ids:
            continue
            
        if not await is_userJoin(client, user_id, ids):
            return False
            
    return True"""
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------


subscribed = filters.create(is_subscribed)
is_admin = filters.create(check_admin)
banUser = filters.create(check_banUser)


#=============================================================================================================================================================================
# -------------------- SEND FILE(S) BY MESSAGE ID(S) -------------------- 
#=============================================================================================================================================================================

from pyrogram.errors import FloodWait, Forbidden, PeerIdInvalid

async def send_file_by_id(client, message, first_msg_id: int, last_msg_id: int = None):
    """
    Send a single file or a batch of files from the DB channel to the user.
    Handles FloodWait, invalid peer, and forbidden errors gracefully.
    """
    try:
        user_id = message.from_user.id
        channel_id = client.db_channel.id

        # If last_msg_id is None, send only one file
        if not last_msg_id or first_msg_id == last_msg_id:
            try:
                await client.copy_message(
                    chat_id=user_id,
                    from_chat_id=channel_id,
                    message_id=first_msg_id
                )
                return
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await client.copy_message(
                    chat_id=user_id,
                    from_chat_id=channel_id,
                    message_id=first_msg_id
                )
            except (Forbidden, PeerIdInvalid):
                await message.reply_text("<b>❌ Cannot send file. User blocked the bot or invalid chat.</b>")
            except Exception as e:
                await message.reply_text(f"<b>⚠️ Failed to send file.</b>\n<code>{e}</code>")
            return

        # If batch range given
        if first_msg_id > last_msg_id:
            first_msg_id, last_msg_id = last_msg_id, first_msg_id

        msg_ids = list(range(first_msg_id, last_msg_id + 1))
        total = len(msg_ids)

        await message.reply_text(f"<b>📤 Sending {total} files...</b>")

        for msg_id in msg_ids:
            try:
                await client.copy_message(
                    chat_id=user_id,
                    from_chat_id=channel_id,
                    message_id=msg_id
                )
                await asyncio.sleep(0.5)  # prevent rate limits
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await client.copy_message(
                    chat_id=user_id,
                    from_chat_id=channel_id,
                    message_id=msg_id
                )
            except Forbidden:
                await message.reply_text("<b>❌ Cannot send file. User blocked the bot.</b>")
                break
            except Exception as e:
                print(f"!Error sending msg {msg_id}: {e}")
                continue

        await message.reply_text("<b>✅ All available files sent successfully!</b>")

    except Exception as e:
        print(f"Error in send_file_by_id(): {e}")
        await message.reply_text("<b>⚠️ Error while sending files.</b>")
