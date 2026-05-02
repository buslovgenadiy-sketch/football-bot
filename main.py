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

        full_text = soup.get_text("\n", strip=True)
        lines = full_text.split("\n")

        start_index = None

        for i, line in enumerate(lines):
            if "Комментарии" in line:
                start_index = i + 1
                break

        if start_index is None:
            return "Текст новини поки не вдалося отримати."

        bad_words = [
            "Поделиться",
            "Комментарии",
            "Материалы по теме",
            "Теги",
            "Источник",
            "Сообщить об ошибке",
            "Заглавное фото",
            "Новости. Футбол",
            "Реклама",
            "Правовая информация",
            "Политика конфиденциальности",
            "На информационном ресурсе",
            "©"
        ]

        good_lines = []

        for line in lines[start_index:]:
            if any(bad.lower() in line.lower() for bad in bad_words):
                break

            if len(line) < 40:
                continue

            good_lines.append(line)

            if len(good_lines) >= 4:
                break

        if good_lines:
            return "\n\n".join(good_lines)

        return "Текст новини поки не вдалося отримати."

    except Exception as e:
        print("Ошибка get_news_text:", e)
        return "Текст новини поки не вдалося отримати."


def get_news_image(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        og_image = soup.find("meta", attrs={"property": "og:image"})

        if og_image:
            image_url = og_image.get("content", "").strip()

            if image_url.startswith("http"):
                return image_url

        return None

    except Exception as e:
        print("Ошибка get_news_image:", e)
        return None


def make_post(title, article_text):
    return f"""🚨 {title}

⚽ {article_text}
"""


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
        image = get_news_image(item["link"])
        text = make_post(item["title"], article_text)

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
            image = get_news_image(item["link"])
            text = make_post(item["title"], article_text)

            if image:
                await bot.send_photo(
                    CHANNEL_ID,
                    photo=image,
                    caption=text[:1024]
                )
            else:
                await bot.send_message(
                    CHANNEL_ID,
                    text
                )

            if call.message.caption:
                await call.message.edit_caption("✅ Опубліковано")
            else:
                await call.message.edit_text("✅ Опубліковано")

    elif data.startswith("skip_"):
        if call.message.caption:
            await call.message.edit_caption("❌ Пропущено")
        else:
            await call.message.edit_text("❌ Пропущено")


async def scheduler():
    while True:
        try:
            await send_news()
        except Exception as e:
            print("Ошибка scheduler:", e)

        await asyncio.sleep(600)


async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
        
