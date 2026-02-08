import whisper
import logging
import torch

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class WhisperASR:
    def __init__(self, model_size: str = "medium"):
        """
        model_size: tiny, base, small, medium, large
        medium = ~6GB VRAM, хороший баланс
        """
        logger.info(f"Загрузка Whisper модели '{model_size}'...")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Устройство: {device}")
        
        self.model = whisper.load_model(model_size, device=device)
        logger.info(f"✅ Модель загружена")
    
    def transcribe(self, audio_path: str, language: str = "ru") -> str:
        """Распознаёт аудио файл, возвращает текст"""
        logger.info(f"Распознавание: {audio_path}")
        
        result = self.model.transcribe(
            audio_path,
            language=language,
            fp16=torch.cuda.is_available()  # float16 для GPU
        )
        
        text = result["text"].strip()
        logger.info(f"✅ Распознано: {text}")
        return text


if __name__ == "__main__":
    # Тест: создайте test.mp3 с записью "Покажи новости про Газпром"
    # Или используйте любой русский аудиофайл
    
    asr = WhisperASR(model_size="base")  # base быстрее для теста
    
    # Если у вас есть аудио файл:
    # text = asr.transcribe("test.mp3")
    # print(f"Результат: {text}")
    
    print("WhisperASR готов к работе!")
