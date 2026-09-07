<img width="1920" height="1080" alt="1" src="https://github.com/user-attachments/assets/24281969-c9ac-41f7-b24a-5e8bf116ed46" />


FinSense — это Telegram-бот для глубокого финансового анализа банковских выписок (PDF и CSV) с интерактивным Telegram Mini App (дашборд) и поддержкой генерации инфографики.


## Основные возможности

- 📄 **Анализ выписок:** Автоматический парсинг выписок основных банков в форматах CSV и PDF.
- 📈 **Инфографика в чате:** Отправка графиков высокого разрешения прямо в переписку.
- 🧠 **ИИ-советник по оптимизации бюджета:** Персонализированные советы по сокращению необязательных ("гибких") расходов без канцелярщины.
- 🎯 **Калькулятор целей накопления:** Расчёт реалистичных сроков накопления на основе свободных денег и сценариев оптимизации расходов.

## Стек технологий

- **Python 3.10+**
- **aiogram 3** — асинхронный фреймворк для Telegram Bot API
- **aiohttp** — легковесный веб-сервер для Telegram Mini App
- **pandas, pdfplumber** — обработка табличных данных и парсинг PDF
- **matplotlib** — генерация визуализаций и графиков в чате
- **OpenAI-compatible / Gemini API** — интеллектуальный анализ и финансовые рекомендации

## Установка и запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/kajduch/finsense.git
cd finsense
```

### 2. Настройка виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate  # Для bash/zsh
# или source venv/bin/activate.fish для fish
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
Создайте файл `.env` на основе примера:
```bash
cp .env.example .env
```
Заполните `.env`:
- `BOT_TOKEN` — токен вашего Telegram-бота от [@BotFather](https://t.me/BotFather).
- `GEMINI_API_KEY` — API-ключ для доступа к нейросети.
- `PROXY_BASE_URL` — адрес API эндпоинта (например, `https://ai.starimg.ru/v1/chat/completions` или официальный Google/OpenAI).

### 5. Запуск бота
```bash
python bot.py
```
