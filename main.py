import asyncio
import re
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

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_news():
    url = "https://www.championat.com/news/football/1.html"
    result = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a", href=True)

        for link in links:
            href = link["href"]
            title = link.get_text(" ", strip=True)

            # Берём только реальные новости с датой в ссылке
            if not re.search(r"/news/football/\d{4}-\d{2}-\d{2}", href):
                continue

            if len(title) < 25:
                continue

            full_link = "https://www.championat.com" + href if href.startswith("/") else href

            if full_link in posted:
                continue

            result.append({
                "title": title,
                "link": full_link
            })

        unique = []
        seen = set()

        for item in result:
            if item["link"] not in seen:
                unique.append(item)
                seen.add(item["link"])

        return unique[:5]

    except Exception as e:
        print("Ошибка get_news:", e)
        return []


def get_news_text(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        meta = soup.find("meta", attrs={"name": "description"})

        if meta:
            text = meta.get("content", "").strip()

            if len(text) > 40:
                return text

        og = soup.find("meta", attrs={"property": "og:description"})

        if og:
            text = og.get("content", "").strip()

            if len(text) > 40:
                return text

        return "Текст новини поки не вдалося отримати."

    except Exception as e:
        print("Ошибка get_news_text:", e)
        return "Текст новини поки не вдалося отримати."


@dp.message()
async def start_handler(message: types.Message):
    global user_id

    if message.text == "/start":
        user_id = message.from_user.id
        await message.answer("✅ Бот активований. Шукаю футбольні новини...")
        await send_news()


async def send_news():
    global user_id, pending_news

    if not user_id:
        return

    news = get_news()

    if not news:
        await bot.send_message(user_id, "Поки не знайшов нових футбольних новин.")
        return

    for i, item in enumerate(news):
        news_id = str(i)
        pending_news[news_id] = item

        article_text = get_news_text(item["link"])

        text = f"""🚨 {item['title']}

⚽ {article_text}
"""

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

        try:
            await bot.send_message(user_id, text, reply_markup=kb)
            posted.add(item["link"])
        except Exception as e:
            print("Ошибка отправки:", e)


@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):
    data = call.data

    if data.startswith("post_"):
        news_id = data.replace("post_", "")

        if news_id in pending_news:
            item = pending_news[news_id]
            article_text = get_news_text(item["link"])

            text = f"""🚨 {item['title']}

⚽ {article_text}
"""

            await bot.send_message(CHANNEL_ID, text)
            await call.message.edit_text("✅ Опубліковано")

    elif data.startswith("skip_"):
        await call.message.edit_text("❌ Пропущено")


async def scheduler():
    while True:
        try:
            await send_news()
        except Exception as e:
            print("Ошибка scheduler:", e)

        await asyncio.sleep(300)


async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
