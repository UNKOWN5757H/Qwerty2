# +++ Made By King [telegram username: @Shidoteshika1] +++

import motor.motor_asyncio
from datetime import datetime, timedelta
from config import DB_URI, DB_NAME


class SidDataBase:
    def __init__(self, DB_URI, DB_NAME):
        self.dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
        self.database = self.dbclient[DB_NAME]

        # Main collections
        self.user_data = self.database["users"]
        self.channel_data = self.database["channels"]
        self.admins_data = self.database["admins"]
        self.banned_user_data = self.database["banned_user"]
        self.autho_user_data = self.database["autho_user"]

        # Settings collections
        self.auto_delete_data = self.database["auto_delete"]
        self.hide_caption_data = self.database["hide_caption"]
        self.protect_content_data = self.database["protect_content"]
        self.channel_button_data = self.database["channel_button"]
        self.del_timer_data = self.database["del_timer"]
        self.channel_button_link_data = self.database["channelButton_link"]

        # Request ForceSub
        self.rqst_fsub_data = self.database["request_forcesub"]
        self.rqst_fsub_Channel_data = self.database["request_forcesub_channel"]
        self.store_reqLink_data = self.database["store_reqLink"]

        # Other configs
        self.variables_data = self.database["variables"]

        # 🔗 Link system
        self.links_data = self.database["links"]

    # ============================================================
    # VARIABLE MANAGEMENT
    # ============================================================
    async def get_variable(self, key, default=None):
        result = await self.variables_data.find_one({"_id": key})
        return result.get("value", default) if result else default

    async def set_variable(self, key, value):
        await self.variables_data.update_one(
            {"_id": key}, {"$set": {"value": value}}, upsert=True
        )

    # ============================================================
    # CHANNEL BUTTON SETTINGS
    # ============================================================
    async def set_channel_button_link(self, button_name: str, button_link: str):
        await self.channel_button_link_data.delete_many({})
        await self.channel_button_link_data.insert_one(
            {"button_name": button_name, "button_link": button_link}
        )

    async def get_channel_button_link(self):
        data = await self.channel_button_link_data.find_one({})
        if data:
            return data.get("button_name"), data.get("button_link")
        return "Join Channel", "https://t.me/btth480p"

    # ============================================================
    # TIMER SETTINGS
    # ============================================================
    async def set_del_timer(self, value: int):
        await self.del_timer_data.update_one({}, {"$set": {"value": value}}, upsert=True)

    async def get_del_timer(self):
        data = await self.del_timer_data.find_one({})
        return data.get("value", 600) if data else 600

    # ============================================================
    # FEATURE SETTINGS
    # ============================================================
    async def _set_bool_setting(self, collection, value: bool):
        await collection.update_one({}, {"$set": {"value": value}}, upsert=True)

    async def _get_bool_setting(self, collection):
        data = await collection.find_one({})
        return data.get("value", False) if data else False

    async def set_auto_delete(self, value: bool):
        await self._set_bool_setting(self.auto_delete_data, value)

    async def get_auto_delete(self):
        return await self._get_bool_setting(self.auto_delete_data)

    async def set_hide_caption(self, value: bool):
        await self._set_bool_setting(self.hide_caption_data, value)

    async def get_hide_caption(self):
        return await self._get_bool_setting(self.hide_caption_data)

    async def set_protect_content(self, value: bool):
        await self._set_bool_setting(self.protect_content_data, value)

    async def get_protect_content(self):
        return await self._get_bool_setting(self.protect_content_data)

    async def set_channel_button(self, value: bool):
        await self._set_bool_setting(self.channel_button_data, value)

    async def get_channel_button(self):
        return await self._get_bool_setting(self.channel_button_data)

    async def set_request_forcesub(self, value: bool):
        await self._set_bool_setting(self.rqst_fsub_data, value)

    async def get_request_forcesub(self):
        return await self._get_bool_setting(self.rqst_fsub_data)

    # ============================================================
    # USER MANAGEMENT
    # ============================================================
    async def present_user(self, user_id: int):
        return bool(await self.user_data.find_one({"_id": user_id}))

    async def add_user(self, user_id: int):
        await self.user_data.insert_one({"_id": user_id})

    async def full_userbase(self):
        docs = await self.user_data.find().to_list(length=None)
        return [doc["_id"] for doc in docs]

    async def del_user(self, user_id: int):
        await self.user_data.delete_one({"_id": user_id})

    # ============================================================
    # CHANNEL MANAGEMENT
    # ============================================================
    async def add_channel(self, channel_id: int):
        if not await self.channel_data.find_one({"_id": channel_id}):
            await self.channel_data.insert_one({"_id": channel_id})

    async def get_all_channels(self):
        docs = await self.channel_data.find().to_list(length=None)
        return [doc["_id"] for doc in docs]

    async def del_channel(self, channel_id: int):
        await self.channel_data.delete_one({"_id": channel_id})

    # ============================================================
    # ADMIN MANAGEMENT
    # ============================================================
    async def add_admin(self, admin_id: int):
        if not await self.admins_data.find_one({"_id": admin_id}):
            await self.admins_data.insert_one({"_id": admin_id})

    async def admin_exist(self, admin_id: int):
        return bool(await self.admins_data.find_one({"_id": admin_id}))

    async def get_all_admins(self):
        docs = await self.admins_data.find().to_list(length=None)
        return [doc["_id"] for doc in docs]

    async def del_admin(self, admin_id: int):
        await self.admins_data.delete_one({"_id": admin_id})

    # ============================================================
    # BAN MANAGEMENT
    # ============================================================
    async def ban_user_exist(self, user_id: int):
        return bool(await self.banned_user_data.find_one({"_id": user_id}))

    async def add_ban_user(self, user_id: int):
        if not await self.ban_user_exist(user_id):
            await self.banned_user_data.insert_one({"_id": user_id})

    async def del_ban_user(self, user_id: int):
        await self.banned_user_data.delete_one({"_id": user_id})

    async def get_ban_users(self):
        docs = await self.banned_user_data.find().to_list(length=None)
        return [doc["_id"] for doc in docs]

    # ============================================================
    # REQUEST FORCE-SUB MANAGEMENT
    # ============================================================
    async def add_reqChannel(self, channel_id: int):
        await self.rqst_fsub_Channel_data.update_one(
            {"_id": channel_id}, {"$setOnInsert": {"user_ids": []}}, upsert=True
        )

    async def reqSent_user(self, channel_id: int, user_id: int):
        await self.rqst_fsub_Channel_data.update_one(
            {"_id": channel_id}, {"$addToSet": {"user_ids": user_id}}, upsert=True
        )

    async def reqSent_user_exist(self, channel_id: int, user_id: int):
        return bool(
            await self.rqst_fsub_Channel_data.find_one(
                {"_id": channel_id, "user_ids": user_id}
            )
        )

    # ============================================================
    # 🔗 LINK MANAGEMENT SYSTEM
    # ============================================================
    async def save_link(self, unique_code: str, start_id: int, end_id: int = None, expires_in_days: int = 7):
        """Store generated link in database."""
        try:
            doc = {
                "unique_code": unique_code,
                "start_msg_id": start_id,
                "end_msg_id": end_id,
                "created_at": datetime.utcnow(),
                "expires_in_days": expires_in_days,
            }
            await self.links_data.update_one(
                {"unique_code": unique_code}, {"$set": doc}, upsert=True
            )
            return True
        except Exception as e:
            print(f"!Error saving link: {e}")
            return False

    async def get_link(self, unique_code: str):
        """Retrieve link data and remove expired entries."""
        try:
            data = await self.links_data.find_one({"unique_code": unique_code})
            if not data:
                return None

            created_at = data.get("created_at")
            expiry_days = data.get("expires_in_days", 7)
            if (datetime.utcnow() - created_at).days > expiry_days:
                await self.links_data.delete_one({"unique_code": unique_code})
                return None
            return data
        except Exception as e:
            print(f"!Error getting link: {e}")
            return None

    async def delete_old_links(self, days: int = 30):
        """Clean up expired links older than X days."""
        try:
            threshold = datetime.utcnow() - timedelta(days=days)
            result = await self.links_data.delete_many({"created_at": {"$lt": threshold}})
            if result.deleted_count > 0:
                print(f"🧹 Deleted {result.deleted_count} old link(s).")
        except Exception as e:
            print(f"!Error deleting old links: {e}")


# Global instance
kingdb = SidDataBase(DB_URI, DB_NAME)
