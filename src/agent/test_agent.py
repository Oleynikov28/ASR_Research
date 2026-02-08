import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agent.graph import NewsAgent
from src.asr.whisper_handler import WhisperASR

def test_text_queries():
    """Тест текстовых запросов"""
    print("\n" + "="*60)
    print("ТЕСТ 1: ТЕКСТОВЫЕ ЗАПРОСЫ")
    print("="*60)
    
    agent = NewsAgent()
    
    queries = [
        "Покажи новости про Газпром",
        "Что нового у Сбербанка",
        "LKOH",
        "новости роснефть",
    ]
    
    for query in queries:
        print(f"\n▶ Запрос: {query}")
        response = agent.run(query)
        print(response)
        print("-" * 60)

def test_voice_query():
    """Тест голосового запроса (если есть аудио файл)"""
    print("\n" + "="*60)
    print("ТЕСТ 2: ГОЛОСОВОЙ ЗАПРОС")
    print("="*60)
    
    audio_file = "test_audio.mp3"  # Замените на ваш файл
    
    if not os.path.exists(audio_file):
        print(f"⚠️ Файл {audio_file} не найден")
        print("Создайте аудио с фразой: 'Покажи новости про Газпром'")
        return
    
    # ASR
    asr = WhisperASR(model_size="base")
    text = asr.transcribe(audio_file)
    
    # Agent
    agent = NewsAgent()
    response = agent.run(text)
    
    print(f"\n{response}")

def test_full_pipeline():
    """Полный pipeline: текст → граф → ответ"""
    print("\n" + "="*60)
    print("ТЕСТ 3: ПОЛНЫЙ PIPELINE")
    print("="*60)
    
    agent = NewsAgent()
    
    query = "Покажи свежие новости про Газпром"
    print(f"\n📝 Запрос: {query}")
    
    response = agent.run(query)
    
    print(f"\n📄 Ответ:\n{response}")

if __name__ == "__main__":
    test_text_queries()
    # test_voice_query()  # Раскомментируйте если есть аудио
    test_full_pipeline()
