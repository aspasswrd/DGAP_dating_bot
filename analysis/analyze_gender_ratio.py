import asyncio
import matplotlib.pyplot as plt
from src.config import get_db_connection


async def fetch_gender_data():
    conn = await get_db_connection()
    data = await conn.fetch("SELECT is_male, COUNT(*) FROM bot.users GROUP BY is_male")
    await conn.close()
    return data


async def plot_gender_ratio():
    data = await fetch_gender_data()
    labels = ['Женщины', 'Мужчины']
    sizes = [0, 0]
    for record in data:
        if record['is_male']:
            sizes[1] = record['count']
        else:
            sizes[0] = record['count']

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999', '#66b3ff'])
    plt.title('Соотношение мужчин и женщин')
    plt.savefig('./../plots/analyze_gender_ratio.png', bbox_inches='tight')


if __name__ == '__main__':
    asyncio.run(plot_gender_ratio())