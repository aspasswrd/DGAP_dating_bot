import asyncio
import matplotlib.pyplot as plt
import pandas as pd
from src.config import get_db_connection


async def fetch_data():
    conn = await get_db_connection()

    likes_query = """
        SELECT user_id, SUM(likes) as total_likes
        FROM (
            SELECT user_id_1 as user_id, 
                   COUNT(*) FILTER (WHERE first_to_second) as likes
            FROM bot.match
            GROUP BY user_id_1
            UNION ALL
            SELECT user_id_2 as user_id, 
                   COUNT(*) FILTER (WHERE second_to_first) as likes
            FROM bot.match
            GROUP BY user_id_2
        ) t
        GROUP BY user_id
    """
    likes = await conn.fetch(likes_query)

    matches_query = """
        SELECT user_id, COUNT(*) as matches
        FROM bot.done_match
        GROUP BY user_id
    """
    matches = await conn.fetch(matches_query)

    await conn.close()
    return (
        pd.DataFrame(likes, columns=['user_id', 'likes']),
        pd.DataFrame(matches, columns=['user_id', 'matches'])
    )


async def plot_correlation():
    likes_df, matches_df = await fetch_data()
    merged_df = pd.merge(likes_df, matches_df, on='user_id', how='left').fillna(0)

    plt.figure(figsize=(10, 6))
    plt.scatter(merged_df['likes'], merged_df['matches'], alpha=0.5)
    plt.xlabel('Лайки')
    plt.ylabel('Завершенные мэтчи')
    plt.title('Корреляция: лайки vs завершенные мэтчи')
    plt.grid(True)
    plt.savefig('./../plots/analyze_likes_matches.png', bbox_inches='tight')


if __name__ == '__main__':
    asyncio.run(plot_correlation())