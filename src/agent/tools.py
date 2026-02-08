import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
import logging
import re
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class NewsSearchTools:
    def __init__(self, stocks_path: str = "data/stocks.json", 
                 news_path: str = "data/news.json"):
        self.stocks_df = pd.read_json(stocks_path)
        self.news_df = pd.read_json(news_path)
        
        # Создаём словарь для обратного поиска
        self.name_to_ticker = {
            name.lower(): ticker 
            for ticker, name in zip(self.stocks_df['ticker'], self.stocks_df['name'])
        }
        
        # Создаём словарь всех вариантов написания
        self.all_variants = {}
        for ticker, name in zip(self.stocks_df['ticker'], self.stocks_df['name']):
            # Добавляем разные варианты
            variants = [
                name.lower(),                    # "газпром"
                ticker.lower(),                  # "gazp"
                ticker.upper(),                  # "GAZP"
            ]
            for variant in variants:
                self.all_variants[variant] = ticker
        
        logger.info(f"Загружено: {len(self.stocks_df)} акций, {len(self.news_df)} новостей")
        logger.info(f"Варианты поиска: {list(self.all_variants.keys())[:10]}...")
    
    def find_ticker(self, query: str) -> Optional[str]:
        """
        Находит тикер в запросе
        "Покажи новости про Газпром" → "GAZP"
        "SBER новости" → "SBER"
        "что с лукойлом" → "LKOH"
        """
        query_lower = query.lower().strip()
        
        logger.info(f"   🔍 Анализ запроса: '{query_lower}'")
        
        # Способ 1: Прямой поиск тикера в тексте (GAZP, SBER)
        # Ищем слова из 3-5 заглавных букв
        ticker_candidates = re.findall(r'\b([A-Z]{3,5})\b', query)
        for candidate in ticker_candidates:
            if candidate in self.stocks_df['ticker'].values:
                logger.info(f"   ✓ Найден тикер напрямую: {candidate}")
                return candidate
        
        # Способ 2: Поиск по всем вариантам (газпром, сбербанк и т.д.)
        for variant, ticker in self.all_variants.items():
            if variant in query_lower:
                logger.info(f"   ✓ Найдено совпадение: '{variant}' → {ticker}")
                return ticker
        
        # Способ 3: Частичное совпадение (газпр → газпром)
        for name, ticker in self.name_to_ticker.items():
            # Ищем подстроки минимум 4 символа
            if len(name) >= 4:
                if name[:4] in query_lower or name in query_lower:
                    logger.info(f"   ✓ Частичное совпадение: '{name}' → {ticker}")
                    return ticker
        
        logger.warning(f"   ✗ Тикер не найден в запросе")
        return None
    
    def search_news(self, ticker: str, limit: int = 10) -> pd.DataFrame:
        """Ищет новости по тикеру"""
        filtered = self.news_df[
            self.news_df['tickers'].apply(lambda x: ticker in x if isinstance(x, list) else False)
        ]
        
        if 'published' in filtered.columns:
            filtered = filtered.sort_values('published', ascending=False)
        
        return filtered.head(limit)
    
    def get_stock_info(self, ticker: str) -> Optional[dict]:
        """Получает информацию об акции"""
        stock = self.stocks_df[self.stocks_df['ticker'] == ticker]
        if stock.empty:
            return None
        return stock.iloc[0].to_dict()


if __name__ == "__main__":
    tools = NewsSearchTools()
    
    print("\n" + "="*60)
    print("ТЕСТ: Поиск тикеров в разных запросах")
    print("="*60)
    
    test_queries = [
        "Покажи новости про Газпром",
        "Что с акциями Сбербанка?",
        "LKOH",
        "новости по лукойл",
        "роснефть прогноз",
        "SBER падает",
        "что там с газпромом",
    ]
    
    for query in test_queries:
        print(f"\n▶ Запрос: '{query}'")
        ticker = tools.find_ticker(query)
        
        if ticker:
            print(f"  ✅ Найден: {ticker}")
            
            # Показываем новости
            news = tools.search_news(ticker, limit=2)
            if not news.empty:
                print(f"  📰 Новостей: {len(news)}")
                for idx, row in news.iterrows():
                    print(f"     • {row['title'][:50]}...")
            else:
                print(f"  📭 Новостей нет")
        else:
            print(f"  ❌ Не найден")
    
    print("\n" + "="*60)
