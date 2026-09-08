import json
import pandas as pd
import requests
from config import GEMINI_API_KEY, PROXY_BASE_URL
import logging

def _call_proxy_api(prompt: str, max_tokens: int = 8192) -> str:
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gemini-3.8-flash",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }
    response = requests.post(PROXY_BASE_URL, headers=headers, json=data, timeout=180)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def safe_json_loads(text: str) -> dict:
    text = text.strip()
    if text.startswith("```json"): text = text[7:]
    elif text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    text = text.strip()
    
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError as decode_err:
        logging.warning(f"JSON обрезан лимитом токенов ({decode_err}), запускаем автовосстановление...")
        last_obj_idx = text.rfind('}')
        if last_obj_idx != -1:
            candidate = text[:last_obj_idx + 1]
            if not candidate.rstrip().endswith(']'):
                candidate += ']}'
            elif not candidate.rstrip().endswith('}'):
                candidate += '}'
            try:
                data = json.loads(candidate, strict=False)
                if isinstance(data, dict):
                    count = len(data.get('transactions', []))
                    logging.info(f"JSON успешно восстановлен! Спасено транзакций: {count}")
                    return data
            except Exception as e:
                logging.error(f"Не удалось восстановить JSON: {e}")
        raise decode_err

def analyze_pdf_statement(pdf_text: str) -> dict:
    if not pdf_text or len(pdf_text.strip()) == 0:
        return {"transactions": [], "initial_balance": 0.0}
        
    prompt = f"""
    Проанализируй текст банковской выписки.
    1. Найди начальный (входящий) остаток на начало периода (если есть, иначе 0.0).
    2. Извлеки все транзакции. Поля: Date (YYYY-MM-DD), Description (переведи на нормальный русский), Category (Супермаркеты, Переводы, Аптеки, Такси и т.д.), Amount (расходы отрицательные), PayeeType ("Человек" или "Организация").
    
    Верни строго компактный JSON без лишних отступов и пробелов (в одну строку или минимально форматированный), чтобы поместились все транзакции:
    {{"initial_balance":1000.50,"transactions":[{{"Date":"2026-07-17","Description":"T-Mobile","Category":"Связь","Amount":-291.00,"PayeeType":"Организация"}}]}}
    Только валидный JSON.
    Текст выписки:
    {pdf_text[:40000]}
    """
    
    try:
        text = _call_proxy_api(prompt, max_tokens=8192)
        return safe_json_loads(text)
    except Exception as e:
        logging.error(f"Ошибка Proxy API (PDF analyze): {e}")
        raise e

def analyze_csv_data(descriptions: list) -> dict:
    if not descriptions:
        return {"mapping": {}}
        
    prompt = f"""
    Входные данные: {descriptions}
    Задача: Переведи названия из списка на нормальный русский язык, определи категорию, определи PayeeType ("Человек" или "Организация").
    
    Верни строго JSON:
    {{
      "mapping": {{
        "оригинальное_название_1": {{"name": "понятное_название", "category": "Категория", "payeeType": "Организация"}}
      }}
    }}
    Только JSON.
    """
    try:
        text = _call_proxy_api(prompt, max_tokens=4096)
        return safe_json_loads(text)
    except Exception as e:
        logging.error(f"Ошибка Proxy API (CSV analyze): {e}")
        raise e

def generate_financial_advice(df: pd.DataFrame, total_income: float, total_expenses: float) -> str:
    """Генерирует совет по сокращению расходов с учетом новых жестких правил."""
    expenses = df[df['Amount'] < 0].copy()
    if expenses.empty:
        return "У вас нет данных о расходах для анализа."
        
    expenses['Amount_Abs'] = expenses['Amount'].abs()
    category_sums = expenses.groupby('Category')['Amount_Abs'].sum().to_dict()
    
    prompt = f"""
    Проанализируй траты пользователя:
    Доходы: {total_income}
    Расходы: {total_expenses}
    Категории расходов: {json.dumps(category_sums, ensure_ascii=False)}
    
    Напиши совет по сокращению расходов, строго соблюдая эти правила:
    1. Разбей текст на небольшие абзацы для легкости чтения.
    2. Приоритет отдавай "гибким" категориям с реальным потенциалом сокращения (такси, доставка, фастфуд, развлечения, подписки).
    3. Игнорируй "обязательные" траты (коммуналка, связь, аренда, продукты базовые, корм для животных, кредиты, аптеки). Не советуй их сокращать.
    4. Если гибких категорий с заметными тратами нет — прямо скажите об этом (например: "У вас почти нет необязательных трат, ваш бюджет уже максимально оптимизирован"), не выдумывайте советы ради советов.
    5. Общайся на "вы", в вежливом и дружелюбном тоне.
    6. КАТЕГОРИЧЕСКИ ЗАПРЕЩАЕТСЯ использовать канцелярские обороты (например, "рекомендуется оптимизировать логистику", "целесообразно пересмотреть структуру"). Пиши просто и живо.
    7. Форматирование для Telegram: НЕ используй решётки (###) и разделители (---). Для заголовков и важных цифр используй жирный шрифт (**текст**). Для списков используй точку (•) или подходящие эмодзи.
    """
    try:
        return _call_proxy_api(prompt).strip()
    except Exception as e:
        logging.error(f"Ошибка Proxy API (Advice): {e}")
        return f"Не удалось сгенерировать совет из-за ошибки сервера:\n{e}"

def process_goal_request(user_text: str, metrics: dict, category_sums: dict, months: float) -> str:
    """Обрабатывает свободный ввод цели и рассчитывает сроки."""
    prompt = f"""
    Пользователь написал сообщение о своей финансовой цели: "{user_text}"
    
    Текущие финансовые метрики (в среднем за {months:.1f} мес.):
    - Средний доход в месяц: {metrics['total_income'] / months:.2f}
    - Средний расход в месяц: {metrics['total_expenses'] / months:.2f}
    - Свободных денег в месяц сейчас: {(metrics['total_income'] - metrics['total_expenses']) / months:.2f}
    - Категории трат: {json.dumps(category_sums, ensure_ascii=False)}
    
    Задачи:
    1. Извлеки из текста Цель (что хочет), Сумму (сколько надо, число) и Срок (если есть, в месяцах).
    2. Если Сумма не указана (или непонятна) - верни только JSON `{{"error": "Пожалуйста, уточните, какая именно сумма вам нужна для достижения этой цели?"}}`
    3. Если Сумма есть, сделай математический расчет:
       - Если свободных денег в месяц <= 0: честно напиши, что при текущих тратах накопить невозможно. Укажи, из каких цифр считал, и предложи, какие именно гибкие категории урезать, чтобы выйти в плюс.
       - Если срок НЕ указан: посчитай, за сколько месяцев накопится сумма при текущем темпе (свободные деньги). 
       - Если срок указан: посчитай, сколько нужно откладывать в месяц, и сравни с текущими свободными деньгами.
    4. В ответе всегда повторяй из каких цифр ты считал (цель, вычтенные суммы, свободные деньги в месяц), чтобы пользователь видел прозрачность.
    5. Дополнительно покажи второй сценарий — насколько сократится срок (или насколько легче будет копить), если урезать гибкие траты (такси, доставка, рестораны), не трогая обязательные.
    6. Если срок выходит нереалистичным, так и скажи ("при текущих тратах к этому сроку цель недостижима").
    7. Разбей текст на удобные абзацы.
    8. Форматирование для Telegram: НЕ используй решётки (###) и разделители (---). Для заголовков и важных цифр используй жирный шрифт (**текст**). Для списков используй точку (•) или подходящие эмодзи.
    
    Формат ответа: Если сумма не найдена, верни JSON. Если найдена - просто сгенерируй финальный человеческий текст для пользователя.
    """
    try:
        text = _call_proxy_api(prompt).strip()
        if text.startswith("{") or text.startswith("```json"):
            # Попытка распарсить как ошибку
            try:
                if text.startswith("```json"): text = text[7:]
                if text.endswith("```"): text = text[:-3]
                data = json.loads(text.strip(), strict=False)
                if "error" in data:
                    return data["error"]
            except:
                pass
        return text
    except Exception as e:
        logging.error(f"Ошибка Proxy API (Goal): {e}")
        return f"Произошла ошибка при расчете цели:\n{e}"
