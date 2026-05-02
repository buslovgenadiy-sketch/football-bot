import asyncio
import feedparser
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8569854292:AAGxfgw4NnycuLPFgDFzZbb5KxnrmrbsdK0"
CHANNEL_ID = -1003786719812

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_id = None
posted = set()
pending_news = {}

RSS = [
    "https://www.goal.com/feeds/en/news",
    "https://www.espn.com/espn/rss/soccer/news"
]


def get_news():
    result = []

    for url in RSS:
        feed = feedparser.parse(url)

        for item in feed.entries[:5]:
            if item.link not in posted:
                result.append({
                    "title": item.title,
                    "link": item.link
                })

    return result[:5]


@dp.message()
async def start_handler(message: types.Message):
    global user_id

    if message.text == "/start":
        user_id = message.from_user.id
        await message.answer("✅ Бот активований. Новини будуть приходити сюди.")


async def send_news():
    global user_id, pending_news

    if not user_id:
        return

    news = get_news()

    for i, item in enumerate(news):
        news_id = str(i)

        pending_news[news_id] = item

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Опублікувати",
                        callback_data=f"post_{news_id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Пропустити",
                        callback_data=f"skip_{news_id}"
                    )
                ]
            ]
        )

        text = f"⚽ {item['title']}\n\n🔗 {item['link']}"

        try:
            await bot.send_message(user_id, text, reply_markup=kb)
        except Exception as e:
            await bot.send_message(user_id, f"Ошибка отправки: {e}")


@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):
    global pending_news, posted

    data = call.data

    if data.startswith("post_"):
        news_id = data.replace("post_", "")

        if news_id in pending_news:
            item = pending_news[news_id]

            text = f"⚽ {item['title']}\n\n🔗 {item['link']}"

            await bot.send_message(CHANNEL_ID, text)

            posted.add(item["link"])

            await call.message.edit_text("✅ Опубліковано")

    elif data.startswith("skip_"):
        await call.message.edit_text("❌ Пропущено")


async def scheduler():
    while True:
        try:
            await send_news()
        except Exception as e:
            if user_id:
                await bot.send_message(user_id, f"Ошибка scheduler: {e}")

        await asyncio.sleep(1800)   # 30 минут


async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
            
        

        
