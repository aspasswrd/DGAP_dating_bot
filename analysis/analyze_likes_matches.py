import asyncio
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats
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

    merged_df['likes'] = pd.to_numeric(merged_df['likes'], errors='coerce').fillna(0).astype(int)
    merged_df['matches'] = pd.to_numeric(merged_df['matches'], errors='coerce').fillna(0).astype(int)

    corr_coef, p_value = stats.pearsonr(merged_df['likes'], merged_df['matches'])

    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")
    plot = sns.regplot(
        x='likes',
        y='matches',
        data=merged_df,
        scatter_kws={'alpha': 0.5, 'color': 'blue'},
        line_kws={'color': 'red', 'linestyle': '--'}
    )

    plt.annotate(
        f'Pearson r = {corr_coef:.2f}\np-value = {p_value:.4f}',
        xy=(0.7, 0.9),
        xycoords='axes fraction',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
    )

    plt.xlabel('Количество лайков', fontsize=12)
    plt.ylabel('Количество мэтчей', fontsize=12)
    plt.title(f'Корреляция между лайками и мэтчами (n={len(merged_df)})', fontsize=14)
    plt.savefig('./../plots/analyze_likes_matches.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("\n[Результаты анализа]")
    print(f"Образцов данных: {len(merged_df)}")
    print(f"Коэффициент корреляции Пирсона: {corr_coef:.3f}")
    print(f"p-value: {p_value:.5f}")

    if p_value < 0.05:
        print("Заключение: Корреляция статистически значима (p < 0.05)")
    else:
        print("Заключение: Корреляция незначима (p >= 0.05)")


if __name__ == '__main__':
    asyncio.run(plot_correlation())