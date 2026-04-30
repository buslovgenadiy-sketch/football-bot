import asyncio
import feedparser
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8569854292:AAGxfgw4NnycuLPFgDFzZbb5KxnrmrbsdK0"

USER_ID = 2065128167
CHANNEL_ID = -1003786719812

bot = Bot(token=TOKEN)
dp = Dispatcher()

posted = set()

RSS = [
    "https://www.goal.com/feeds/en/news",
    "https://www.espn.com/espn/rss/soccer/news"
]


def get_news():
    arr = []

    for url in RSS:
        feed = feedparser.parse(url)

        for e in feed.entries[:5]:
            if e.link not in posted:
                arr.append({
                    "title": e.title,
                    "link": e.link
                })

    return arr[:5]


async def send_news():
    news = get_news()

    for item in news:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Опублікувати",
                        callback_data=f"post|{item['link']}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Пропустити",
                        callback_data="skip"
                    )
                ]
            ]
        )

        text = f"⚽ {item['title']}\n\n🔗 {item['link']}"

        await bot.send_message(USER_ID, text, reply_markup=kb)


@dp.callback_query()
async def callback(call: types.CallbackQuery):
    data = call.data

    if data.startswith("post|"):
        await bot.send_message(CHANNEL_ID, call.message.text)
        posted.add(data.split("|")[1])
        await call.message.edit_text("✅ Опубліковано")

    else:
        await call.message.edit_text("❌ Пропущено")


async def scheduler():
    while True:
        await send_news()
        await asyncio.sleep(1800)


async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
