import asyncio
import matplotlib.pyplot as plt
from src.config import get_db_connection

async def fetch_age_data():
    conn = await get_db_connection()
    query = """
        SELECT u1.age AS age1, u2.age AS age2
        FROM bot.done_match dm
        JOIN bot.users u1 ON dm.user_id = u1.user_id
        JOIN bot.users u2 ON dm.user_id_with = u2.user_id
    """
    data = await conn.fetch(query)
    await conn.close()
    return [abs(record['age1'] - record['age2']) for record in data]


async def plot_age_diff():
    age_diffs = await fetch_age_data()

    plt.figure(figsize=(10, 6))
    plt.hist(age_diffs, bins=20, color='#4CAF50', edgecolor='black')
    plt.xlabel('Разница в возрасте (лет)')
    plt.ylabel('Количество пар')
    plt.title('Распределение разницы в возрасте')
    plt.axvline(x=10, color='red', linestyle='--', label='Порог 10 лет')
    plt.legend()
    plt.savefig('./../plots/analyze_age_diff.png', bbox_inches='tight')


if __name__ == '__main__':
    asyncio.run(plot_age_diff())