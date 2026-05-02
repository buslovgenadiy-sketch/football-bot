import asyncio
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8569854292:AAGxfgw4NnycuLPFgDFzZbb5KxnrmrbsdK0"
CHANNEL_ID = -1003786719812

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_id = None
posted = set()
pending_news = {}


def get_news():
    result = []

    url = "https://www.championat.com/news/football/1.html"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a")

        for link in links:
            title = link.get_text(strip=True)
            href = link.get("href")

            if not title:
                continue

            if len(title) < 25:
                continue

            if not href:
                continue

            if "/news/" not in href:
                continue

            full_link = "https://www.championat.com" + href if href.startswith("/") else href

            if full_link not in posted:
                result.append({
                    "title": title,
                    "link": full_link
                })

        unique = []
        seen = set()

        for item in result:
            if item["title"] not in seen:
                unique.append(item)
                seen.add(item["title"])

        return unique[:5]

    except:
        return []


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

        text = f"🚨 {item['title']}"

        try:
            await bot.send_message(user_id, text, reply_markup=kb)
            posted.add(item["link"])
        except Exception as e:
            await bot.send_message(user_id, f"Ошибка отправки: {e}")


@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):
    global pending_news

    data = call.data

    if data.startswith("post_"):
        news_id = data.replace("post_", "")

        if news_id in pending_news:
            item = pending_news[news_id]

            text = f"🚨 {item['title']}"

            await bot.send_message(CHANNEL_ID, text)

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

        await asyncio.sleep(1800)


async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
        
