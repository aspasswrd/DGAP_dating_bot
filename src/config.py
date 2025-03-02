import os
from dotenv import load_dotenv
import asyncpg
from aiogram import Bot
import aiohttp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

bot = Bot(BOT_TOKEN)

async def get_db_connection():
    return await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

async def upload_image(img):
    url = 'https://api.imgur.com/3/image'
    headers = {'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'}

    async with aiohttp.ClientSession() as session:
        data = {'image': img}
        async with session.post(url, headers=headers, data=data) as response:
            if response.status == 200:
                result = await response.json()
                image_url = result['data']['link']
                return image_url
            else:
                return None