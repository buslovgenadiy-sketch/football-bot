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


# Получаем список футбольных новостей
def get_news():

    url = "https://www.championat.com/news/football/1.html"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    result = []

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a", href=True)

        for link in links:
            href = link["href"]
            title = link.get_text(strip=True)

            if "/news/football/" not in href:
                continue

            if len(title) < 20:
                continue

            full_link = "https://www.championat.com" + href

            if full_link not in posted:
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

    except:
        return []


# Получаем текст новости
def get_news_text(url):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")

        text_parts = []

        for p in paragraphs:
            txt = p.get_text(strip=True)

            if len(txt) > 50:
                text_parts.append(txt)

        return " ".join(text_parts[:2])

    except:
        return "Подробности уточняются."


@dp.message()
async def start_handler(message: types.Message):
    global user_id

    if message.text == "/start":
        user_id = message.from_user.id
        await message.answer("✅ Бот активований.")
        await send_news()


async def send_news():
    global user_id, pending_news

    if not user_id:
        return

    news = get_news()

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
        except:
            pass


@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):
    global pending_news

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
        except:
            pass

        await asyncio.sleep(300)


async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
                    
    
            


