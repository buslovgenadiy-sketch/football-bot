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

is_running = True  # 🔥 управление ботом

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_news():
    url = "https://www.championat.com/news/football/1.html"
    result = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.select("a[href]"):
            href = link.get("href")
            title = link.get_text(" ", strip=True)

            if not href or not title:
                continue

            if not href.startswith("/football/news-"):
                continue

            if ".html" not in href:
                continue

            if len(title) < 25:
                continue

            full_link = "https://www.championat.com" + href

            if full_link in posted:
                continue

            result.append({
                "title": title,
                "link": full_link
            })

            if len(result) >= 5:
                break

        return result

    except:
        return []


def get_news_text(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        full_text = soup.get_text("\n", strip=True)
        lines = full_text.split("\n")

        start_index = None

        for i, line in enumerate(lines):
            if "Комментарии" in line:
                start_index = i + 1
                break

        if start_index is None:
            return "Текст не знайдено."

        good_lines = []

        for line in lines[start_index:]:
            if len(line) < 40:
                continue

            good_lines.append(line)

            if len(good_lines) >= 3:
                break

        return "\n\n".join(good_lines)

    except:
        return "Текст не знайдено."


def get_news_image(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        og_image = soup.find("meta", attrs={"property": "og:image"})

        if og_image:
            return og_image.get("content")

        return None

    except:
        return None


def make_post(title, text):
    return f"""🚨 {title}

⚽ {text}
"""


@dp.message()
async def handler(message: types.Message):
    global user_id, is_running

    if message.text == "/start":
        user_id = message.from_user.id
        await message.answer("✅ Бот активований")

    elif message.text == "/on":
        is_running = True
        await message.answer("🟢 Бот увімкнено")

    elif message.text == "/off":
        is_running = False
        await message.answer("🔴 Бот вимкнено")


async def send_news():
    global user_id, pending_news

    if not user_id:
        return

    news = get_news()

    for i, item in enumerate(news):
        news_id = str(i)
        pending_news[news_id] = item

        text_data = get_news_text(item["link"])
        image = get_news_image(item["link"])

        text = make_post(item["title"], text_data)

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
            if image:
                await bot.send_photo(
                    user_id,
                    photo=image,
                    caption=text[:1024],
                    reply_markup=kb
                )
            else:
                await bot.send_message(
                    user_id,
                    text,
                    reply_markup=kb
                )

            posted.add(item["link"])

        except:
            pass


@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):
    data = call.data

    if data.startswith("post_"):
        news_id = data.replace("post_", "")

        if news_id in pending_news:
            item = pending_news[news_id]

            text_data = get_news_text(item["link"])
            image = get_news_image(item["link"])

            text = make_post(item["title"], text_data)

            if image:
                await bot.send_photo(
                    CHANNEL_ID,
                    photo=image,
                    caption=text[:1024]
                )
            else:
                await bot.send_message(CHANNEL_ID, text)

            await call.message.edit_caption("✅ Опубліковано") if call.message.caption else await call.message.edit_text("✅ Опубліковано")

    elif data.startswith("skip_"):
        await call.message.edit_caption("❌ Пропущено") if call.message.caption else await call.message.edit_text("❌ Пропущено")


async def scheduler():
    global is_running

    while True:
        if is_running:
            await send_news()

        await asyncio.sleep(600)


async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
                                        
