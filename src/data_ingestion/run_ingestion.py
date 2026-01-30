import os
import sys
import logging
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.data_ingestion.moex_service import MOEXService
from src.data_ingestion.rss_service import RSSService

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def save_dataframe(df: pd.DataFrame, filename: str):
    """Сохраняет DataFrame в JSON"""
    os.makedirs('data', exist_ok=True)
    path = os.path.join('data', filename)
    df.to_json(path, orient='records', force_ascii=False, indent=2)
    logger.info(f"💾 {path}: {len(df)} записей")


def main():
    print("\n" + "="*60)
    print("ЭТАП 1: СБОР ДАННЫХ")
    print("="*60 + "\n")
    
    logger.info("1. Запрос акций с MOEX...")
    stocks_df = MOEXService.get_top_stocks(limit=60)
    
    if stocks_df.empty:
        logger.error("❌ Не удалось получить акции")
        return
    
    save_dataframe(stocks_df, 'stocks.json')
    logger.info(f"   Примеры: {stocks_df['ticker'].head(3).tolist()}\n")
    
    logger.info("2. Сбор новостей из RSS...")
    rss = RSSService(stocks_df)
    news_df = rss.fetch_all_news(max_per_source=30)
    
    save_dataframe(news_df, 'news.json')
    
    news_with_tickers = news_df[news_df['tickers'].apply(len) > 0]
    
    print("\n" + "="*60)
    print("✅ ГОТОВО")
    print("="*60)
    print(f"Акций: {len(stocks_df)}")
    print(f"Новостей: {len(news_df)}")
    print(f"С тикерами: {len(news_with_tickers)}")
    
    if not news_with_tickers.empty:
        all_tickers = [t for tickers in news_with_tickers['tickers'] for t in tickers]
        ticker_counts = pd.Series(all_tickers).value_counts()
        print(f"\nТоп-5 упоминаемых акций:")
        for ticker, count in ticker_counts.head(5).items():
            print(f"  {ticker}: {count} новостей")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
