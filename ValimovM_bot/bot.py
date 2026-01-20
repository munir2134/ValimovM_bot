import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

# Вставь сюда свой токен от BotFather
TOKEN = "8538204119:AAH77nsx0JrDOcc0MxAz6EnHiGPHvMq-s4I"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Папка для загрузок
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Словарь для хранения ссылок пользователей
user_links = {}


# Приветствие
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🦖 Привет! Я ValimovM bot\n\n"
        "Пришли ссылку на YouTube 🎬"
    )


# Получение ссылки
@dp.message()
async def get_link(message: types.Message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("❌ Пришли корректную ссылку на YouTube")
        return

    user_links[message.from_user.id] = url

    # Кнопки для выбора формата
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎥 Видео", callback_data="video"),
            InlineKeyboardButton(text="🎵 Аудио (MP3)", callback_data="audio")
        ]
    ])
    await message.answer("Что скачать?", reply_markup=keyboard)


# Обработка кнопок
@dp.callback_query()
async def download(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    url = user_links.get(user_id)

    if not url:
        await callback.message.answer("❌ Сначала пришли ссылку на видео")
        return

    await callback.message.answer("⏳ Скачиваю, подожди...")

    try:
        if callback.data == "video":
            ydl_opts = {
                "format": "mp4",
                "outtmpl": f"{DOWNLOADS_DIR}/%(title)s.%(ext)s",
                "quiet": True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            await callback.message.answer_video(
                video=types.FSInputFile(filename),
                caption="✅ Видео готово"
            )

        elif callback.data == "audio":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{DOWNLOADS_DIR}/%(title)s.%(ext)s",
                "quiet": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = f"{DOWNLOADS_DIR}/{info['title']}.mp3"

            await callback.message.answer_audio(
                audio=types.FSInputFile(filename),
                caption="🎵 MP3 готово"
            )

        # Удаляем файл после отправки
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")

    await callback.answer()


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
