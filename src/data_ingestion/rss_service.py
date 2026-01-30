import feedparser
import re
import logging
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class RSSService:
    # Источники, которые пишут про акции и компании
    FEED_URLS = {
        'cbr': 'http://www.cbr.ru/rss/RssNews',
        'investfunds': 'https://www.investfunds.ru/news/rss/',
        'smart_lab': 'https://smart-lab.ru/rss/',
    }
    
    def __init__(self, stocks_df: pd.DataFrame):
        self.known_tickers = set(stocks_df['ticker'].values)
        
        # Создаём несколько вариантов для поиска
        self.ticker_variants = {}
        for ticker, name in zip(stocks_df['ticker'], stocks_df['name']):
            # Все варианты в нижнем регистре для поиска
            variants = [
                name.lower(),           # "газпром"
                name.upper(),           # "ГАЗПРОМ"
                ticker.lower(),         # "gazp"
                ticker.upper(),         # "GAZP"
            ]
            for variant in variants:
                self.ticker_variants[variant] = ticker
        
        logger.info(f"Инициализирован с {len(self.known_tickers)} тикерами")
        logger.info(f"Варианты поиска: {list(self.ticker_variants.keys())[:10]}...")
    
    def _extract_tickers(self, text: str) -> list:
        if not text:
            return []
        
        found = set()
        
        # Способ 1: Прямой поиск тикеров (GAZP, SBER)
        for candidate in re.findall(r'\b([A-Z]{3,5})\b', text):
            if candidate in self.known_tickers:
                found.add(candidate)
        
        # Способ 2: Поиск по всем вариантам (регистронезависимо)
        text_lower = text.lower()
        for variant, ticker in self.ticker_variants.items():
            if variant.lower() in text_lower:
                found.add(ticker)
                logger.debug(f"    Найден '{variant}' → {ticker}")
        
        return list(found)
    
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def fetch_all_news(self, max_per_source: int = 30, use_mock_if_empty: bool = True) -> pd.DataFrame:
        """Собирает новости из RSS"""
        all_news = []
        
        logger.info("\n📡 Сбор новостей из RSS...")
        
        for source_name, feed_url in self.FEED_URLS.items():
            logger.info(f"\n  {source_name}: {feed_url}")
            
            try:
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:
                    logger.warning(f"    ⚠️ Парсинг с ошибками: {feed.bozo_exception}")
                
                entries_count = len(feed.entries)
                logger.info(f"    📄 Записей: {entries_count}")
                
                if entries_count == 0:
                    continue
                
                collected = 0
                tickers_found = 0
                
                for entry in feed.entries[:max_per_source]:
                    title = self._clean_text(entry.get('title', ''))
                    summary = self._clean_text(entry.get('summary', entry.get('description', '')))
                    
                    if not title:
                        continue
                    
                    full_text = f"{title} {summary}"
                    tickers = self._extract_tickers(full_text)
                    
                    all_news.append({
                        'title': title[:200],
                        'link': entry.get('link', ''),
                        'published': entry.get('published', datetime.now().isoformat()),
                        'source': source_name,
                        'tickers': tickers,
                        'summary': summary[:500]
                    })
                    collected += 1
                    
                    if tickers:
                        tickers_found += 1
                        logger.info(f"    ✅ [{', '.join(tickers)}] {title[:45]}...")
                
                logger.info(f"    📊 Собрано: {collected}, с тикерами: {tickers_found}")
                
            except Exception as e:
                logger.error(f"    ❌ Ошибка: {e}")
        
        # Если не нашли новости с тикерами - добавляем mock данные
        news_with_tickers_count = len([n for n in all_news if n['tickers']])
        
        if news_with_tickers_count == 0 and use_mock_if_empty:
            logger.warning("\n⚠️ Не найдено новостей с тикерами!")
            logger.warning("Добавляем тестовые данные для демонстрации...")
            all_news.extend(self._create_mock_news())
        
        df = pd.DataFrame(all_news)
        
        if not df.empty:
            news_with_tickers = df[df['tickers'].apply(len) > 0]
            logger.info(f"\n📊 ИТОГО:")
            logger.info(f"  Всего: {len(df)}")
            logger.info(f"  С тикерами: {len(news_with_tickers)}")
            
            if not news_with_tickers.empty:
                ticker_list = [t for tickers in news_with_tickers['tickers'] for t in tickers]
                unique_tickers = set(ticker_list)
                logger.info(f"  Найдены тикеры: {', '.join(sorted(unique_tickers))}")
        
        return df
    
    def _create_mock_news(self) -> list:
        """Тестовые новости для демо"""
        return [
            {
                'title': 'Газпром увеличил добычу газа на 15% в январе',
                'link': 'https://example.com/mock/1',
                'published': '2026-01-30T10:00:00',
                'source': 'mock_data',
                'tickers': ['GAZP'],
                'summary': 'ПАО Газпром сообщило об увеличении добычи природного газа на 15% по сравнению с аналогичным периодом прошлого года'
            },
            {
                'title': 'Сбербанк показал рекордную прибыль за 2025 год',
                'link': 'https://example.com/mock/2',
                'published': '2026-01-30T11:00:00',
                'source': 'mock_data',
                'tickers': ['SBER'],
                'summary': 'Крупнейший банк России Сбербанк опубликовал финансовые результаты, показав рекордную прибыль'
            },
            {
                'title': 'Лукойл планирует увеличить инвестиции в разведку',
                'link': 'https://example.com/mock/3',
                'published': '2026-01-30T12:00:00',
                'source': 'mock_data',
                'tickers': ['LKOH'],
                'summary': 'Нефтяная компания Лукойл объявила о планах по увеличению капитальных вложений в геологоразведку'
            },
            {
                'title': 'Роснефть и Газпром подписали новое соглашение',
                'link': 'https://example.com/mock/4',
                'published': '2026-01-30T13:00:00',
                'source': 'mock_data',
                'tickers': ['ROSN', 'GAZP'],
                'summary': 'Роснефть и Газпром договорились о совместной разработке месторождения'
            },
            {
                'title': 'Татнефть начала новый проект в Западной Сибири',
                'link': 'https://example.com/mock/5',
                'published': '2026-01-30T14:00:00',
                'source': 'mock_data',
                'tickers': ['TATN'],
                'summary': 'Татнефть приступила к реализации крупного проекта по добыче нефти'
            },
            {
                'title': 'Аналитики повысили прогноз по акциям Новатэк',
                'link': 'https://example.com/mock/6',
                'published': '2026-01-30T15:00:00',
                'source': 'mock_data',
                'tickers': ['NVTK'],
                'summary': 'Ведущие аналитические агентства улучшили рекомендации по акциям Новатэк'
            },
            {
                'title': 'ЦБ РФ сохранил ключевую ставку на уровне 21%',
                'link': 'https://example.com/mock/7',
                'published': '2026-01-30T16:00:00',
                'source': 'mock_data',
                'tickers': [],
                'summary': 'Совет директоров Банка России принял решение сохранить ключевую ставку без изменений'
            },
        ]


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ RSS SERVICE")
    print("="*60)
    
    test_stocks = pd.DataFrame({
        'ticker': ['GAZP', 'SBER', 'LKOH', 'ROSN', 'TATN', 'NVTK'],
        'name': ['Газпром', 'Сбербанк', 'Лукойл', 'Роснефть', 'Татнефть', 'Новатэк'],
        'price': [150.0, 250.0, 5000.0, 450.0, 600.0, 1100.0]
    })
    
    rss = RSSService(test_stocks)
    df = rss.fetch_all_news(max_per_source=20, use_mock_if_empty=True)
    
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТ")
    print("="*60)
    
    if not df.empty:
        print(f"\nВсего новостей: {len(df)}")
        
        news_with_tickers = df[df['tickers'].apply(len) > 0]
        print(f"С тикерами: {len(news_with_tickers)}")
        
        if not news_with_tickers.empty:
            print(f"\n{'='*60}")
            print("НОВОСТИ С ТИКЕРАМИ:")
            print('='*60)
            for idx, row in news_with_tickers.head(10).iterrows():
                print(f"\n[{row['source']}] [{', '.join(row['tickers'])}]")
                print(f"  {row['title']}")
                print(f"  🔗 {row['link'][:50]}...")
