import asyncio
from bot import Bot

async def main():
    bot = Bot()
    await bot.start()
    print("Bot started successfully — waiting forever.")
    await asyncio.Event().wait()  # Keeps process alive

if __name__ == "__main__":
    asyncio.run(main())
