import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import logging
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from src.agent.tools import NewsSearchTools

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Состояние графа (передаётся между узлами)
class AgentState(TypedDict):
    query: str                      # Запрос пользователя
    ticker: str                     # Найденный тикер
    stock_info: dict               # Информация об акции
    news: list                     # Найденные новости
    response: str                  # Итоговый ответ

class NewsAgent:
    def __init__(self):
        self.tools = NewsSearchTools()
        self.graph = self._build_graph()
    
    def _extract_ticker(self, state: AgentState) -> AgentState:
        """Узел 1: Извлекает тикер из запроса"""
        query = state["query"]
        logger.info(f"\n1️⃣ Извлечение тикера из: '{query}'")
        
        ticker = self.tools.find_ticker(query)
        
        if ticker:
            logger.info(f"   ✅ Найден тикер: {ticker}")
            state["ticker"] = ticker
        else:
            logger.warning(f"   ⚠️ Тикер не найден")
            state["ticker"] = None
        
        return state
    
    def _search_news(self, state: AgentState) -> AgentState:
        """Узел 2: Ищет новости по тикеру"""
        ticker = state.get("ticker")
        
        if not ticker:
            logger.warning("2️⃣ Пропускаем поиск (нет тикера)")
            state["news"] = []
            return state
        
        logger.info(f"\n2️⃣ Поиск новостей по {ticker}...")
        
        # Получаем информацию об акции
        stock_info = self.tools.get_stock_info(ticker)
        state["stock_info"] = stock_info
        
        # Ищем новости
        news_df = self.tools.search_news(ticker, limit=10)
        state["news"] = news_df.to_dict('records') if not news_df.empty else []
        
        logger.info(f"   ✅ Найдено новостей: {len(state['news'])}")
        
        return state
    
    def _format_response(self, state: AgentState) -> AgentState:
        """Узел 3: Форматирует ответ для пользователя"""
        logger.info(f"\n3️⃣ Форматирование ответа...")
        
        ticker = state.get("ticker")
        stock_info = state.get("stock_info")
        news_list = state.get("news", [])
        
        if not ticker:
            state["response"] = "❌ Не удалось определить компанию. Попробуйте: 'Покажи новости про Газпром'"
            return state
        
        if not news_list:
            state["response"] = f"📭 Новостей по {ticker} ({stock_info['name']}) не найдено"
            return state
        
        # Форматируем красивый ответ
        response_lines = [
            f"📊 Новости по {ticker} ({stock_info['name']})",
            f"💰 Цена: {stock_info['price']:.2f} ₽",
            f"📰 Найдено новостей: {len(news_list)}\n"
        ]
        
        for i, news in enumerate(news_list[:5], 1):
            response_lines.append(f"{i}. [{news['source']}] {news['title']}")
            response_lines.append(f"   🔗 {news['link']}")
            response_lines.append("")
        
        state["response"] = "\n".join(response_lines)
        logger.info("   ✅ Ответ сформирован")
        
        return state
    
    def _build_graph(self) -> StateGraph:
        """Создаёт граф обработки"""
        workflow = StateGraph(AgentState)
        
        # Добавляем узлы
        workflow.add_node("extract_ticker", self._extract_ticker)
        workflow.add_node("search_news", self._search_news)
        workflow.add_node("format_response", self._format_response)
        
        # Связываем узлы
        workflow.set_entry_point("extract_ticker")
        workflow.add_edge("extract_ticker", "search_news")
        workflow.add_edge("search_news", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    def run(self, query: str) -> str:
        """Главный метод: принимает запрос, возвращает ответ"""
        logger.info(f"\n{'='*60}")
        logger.info(f"ЗАПРОС: {query}")
        logger.info('='*60)
        
        initial_state = {
            "query": query,
            "ticker": None,
            "stock_info": None,
            "news": [],
            "response": ""
        }
        
        final_state = self.graph.invoke(initial_state)
        
        logger.info(f"\n{'='*60}")
        logger.info("РЕЗУЛЬТАТ:")
        logger.info('='*60)
        
        return final_state["response"]


if __name__ == "__main__":
    agent = NewsAgent()
    
    # Тесты
    test_queries = [
        "Покажи новости про Газпром",
        "SBER",
        "новости лукойл",
        "что с роснефтью",
        "биткоин"  # Должен не найти
    ]
    
    for query in test_queries:
        response = agent.run(query)
        print(f"\n{response}\n")
        print("-" * 60)
