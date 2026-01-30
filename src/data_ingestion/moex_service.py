import requests
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class MOEXService:
    BASE_URL = "https://iss.moex.com/iss"
    
    @staticmethod
    def get_top_stocks(limit: int = 60) -> pd.DataFrame:
        """Возвращает DataFrame с колонками: ticker, name, price"""
        try:
            url = f"{MOEXService.BASE_URL}/engines/stock/markets/shares/boards/TQBR/securities.json"
            response = requests.get(url, params={'limit': limit}, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            columns = data['securities']['columns']
            rows = data['securities']['data']
            
            secid_idx = columns.index('SECID')
            name_idx = columns.index('SHORTNAME')
            price_idx = columns.index('PREVPRICE')
            
            stocks_data = []
            for row in rows:
                if row[name_idx] and row[price_idx]:
                    stocks_data.append({
                        'ticker': row[secid_idx],
                        'name': row[name_idx],
                        'price': float(row[price_idx])
                    })
            
            df = pd.DataFrame(stocks_data)
            logger.info(f"✅ Получено {len(df)} акций с MOEX")
            return df
            
        except Exception as e:
            logger.error(f"❌ Ошибка MOEX API: {e}")
            return pd.DataFrame(columns=['ticker', 'name', 'price'])


if __name__ == "__main__":
    df = MOEXService.get_top_stocks(limit=10)
    print(df.head())
    print(f"\nТипы: {df.dtypes}")
