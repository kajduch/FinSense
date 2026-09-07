import re
import asyncio

import uuid
import threading
import subprocess
import time
from aiohttp import web
import aiohttp_cors
import math
from aiogram.types.web_app_info import WebAppInfo

USER_DATA = {}
WEBAPP_URL = "https://localhost:8080"

import math
import numpy as np

def clean_nan(obj):
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, (float, np.floating)):
        if math.isnan(obj) or np.isnan(obj) or np.isinf(obj):
            return None
    elif not isinstance(obj, (list, dict, str)) and pd.isna(obj):
        return None
    return obj

def run_tunnel():
    global WEBAPP_URL
    while True:
        logging.info("Starting localhost.run SSH tunnel...")
        proc = subprocess.Popen(
            ['ssh', '-R', '80:localhost:8080', '-o', 'StrictHostKeyChecking=no', 'nokey@localhost.run'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in iter(proc.stdout.readline, ''):
            match = re.search(r'https://[a-zA-Z0-9.-]+\.lhr\.life', line)
            if match:
                WEBAPP_URL = match.group(0)
                logging.info(f"New Tunnel URL: {WEBAPP_URL}")
        proc.wait()
        logging.warning("Tunnel closed. Restarting in 3s...")
        time.sleep(3)

async def index(request):
    session_id = request.query.get('session_id')
    with open('templates/index.html', 'r') as f:
        html = f.read()
    
    if session_id and session_id in USER_DATA:
        import json
        try:
            data_json = json.dumps(USER_DATA[session_id], ensure_ascii=False)
            data_json = data_json.replace("</", r"<\/")
            html = html.replace('window.INITIAL_DATA = null;', f'window.INITIAL_DATA = {data_json};')
        except Exception as e:
            logging.error(f"JSON serialization error: {e}")
            html = html.replace('window.INITIAL_DATA = null;', f'window.INITIAL_DATA = "ERROR: {e}";')
            
    return web.Response(text=html, content_type='text/html')

async def get_data(request):
    session_id = request.query.get('session_id')
    if not session_id or session_id not in USER_DATA:
        return web.json_response({"error": "No data found"}, status=404)
    return web.json_response(USER_DATA[session_id])

async def start_webapp():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/api/data', get_data)
    
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")
    })
    for route in list(app.router.routes()):
        cors.add(route)
        
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logging.info("WebApp running on port 8080")

import logging
import pandas as pd
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN
from parser import parse_bank_statement_csv, extract_text_from_pdf
from analytics import (
    generate_spending_pie_chart, 
    generate_balance_dynamics, 
    generate_top_payees_bar_chart,
)
from ai_assistant import (
    analyze_pdf_statement, 
    analyze_csv_data, 
    generate_financial_advice,
    process_goal_request
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class GoalForm(StatesGroup):
    amount = State()

import time
def get_action_keyboard(session_id: str = None):
    builder = InlineKeyboardBuilder()
    if session_id:
        ts = int(time.time())
        builder.button(text="⚡ Открыть дашборд", web_app=WebAppInfo(url=f"{WEBAPP_URL}?session_id={session_id}&v={ts}"))
    builder.button(text="📊 Категории расходов", callback_data="show_pie")
    builder.button(text="📈 Динамика баланса", callback_data="show_balance")
    builder.button(text="🏢 Топ-5 (Организации)", callback_data="show_payees_org")
    builder.button(text="👤 Топ-5 (Переводы людям)", callback_data="show_payees_person")
    builder.button(text="💡 Финансовый совет ИИ", callback_data="show_advice")
    builder.button(text="🎯 Накопить на цель", callback_data="goal_setup")
    builder.button(text="📑 Показать всё", callback_data="show_all")
    builder.adjust(1)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "Привет! Я **FinSense**, твой личный финансовый ИИ-ассистент. 🤖💸\n\n"
        "Отправьте мне файл банковской выписки в формате `.csv` или `.pdf`.\n"
        "Вы можете загрузить выписку за любой период. Однако, если вы хотите проанализировать данные за несколько месяцев в формате CSV, "
        "пожалуйста, объедините их в один файл заранее — я анализирую только один присланный файл за раз.\n\n"
        "Жду вашу выписку!"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(F.document)
async def handle_document(message: Message, state: FSMContext):
    file_name = message.document.file_name.lower()
    if not (file_name.endswith('.csv') or file_name.endswith('.pdf')):
        await message.answer("Пожалуйста, отправьте файл в формате CSV или PDF.")
        return

    msg = await message.answer("Файл получен. Начинаю глубокий анализ с помощью AI... 🧠 (Это может занять некоторое время)")
    
    try:
        file_io = await bot.download(message.document)
        file_content = file_io.read()
        
        df = pd.DataFrame()
        metrics = {}
        initial_balance = 0.0
        
        if file_name.endswith('.csv'):
            df, metrics = parse_bank_statement_csv(file_content)
            if df.empty:
                await msg.edit_text("Не удалось найти транзакции в CSV.")
                return
                
            initial_balance = metrics.get('initial_balance', 0.0)
            unique_descs = df['Description'].unique().tolist()
            top_descs = unique_descs[:50]
            
            ai_data = analyze_csv_data(top_descs)
            mapping = ai_data.get('mapping', {})
            
            df['PayeeType'] = 'Организация'
            if mapping:
                def update_row(row):
                    orig_desc = row['Description']
                    if orig_desc in mapping:
                        data = mapping[orig_desc]
                        if isinstance(data, dict):
                            row['Description'] = data.get('name', orig_desc)
                            row['Category'] = data.get('category', row['Category'])
                            row['PayeeType'] = data.get('payeeType', 'Организация')
                        elif isinstance(data, str):
                            row['Description'] = data
                    return row
                df = df.apply(update_row, axis=1)

        elif file_name.endswith('.pdf'):
            text = extract_text_from_pdf(file_content)
            if not text.strip():
                await msg.edit_text("Не удалось извлечь текст из PDF.")
                return
                
            ai_data = analyze_pdf_statement(text)
            transactions = ai_data.get('transactions', [])
            initial_balance = ai_data.get('initial_balance', 0.0)
            
            if not transactions:
                await msg.edit_text("Не удалось распознать транзакции в PDF файле.")
                return
                
            df = pd.DataFrame(transactions)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            if 'Category' not in df.columns:
                df['Category'] = 'Неизвестно'
            if 'PayeeType' not in df.columns:
                df['PayeeType'] = 'Организация'
                
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0.0)
            df = df.dropna(subset=['Date'])
            
            # Считаем метрики для PDF
            total_income = df[df['Amount'] > 0]['Amount'].sum()
            total_expenses = df[df['Amount'] < 0]['Amount'].sum()
            min_date = df['Date'].min().strftime('%d.%m.%Y')
            max_date = df['Date'].max().strftime('%d.%m.%Y')
            
            metrics = {
                "initial_balance": initial_balance,
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
                "final_balance": initial_balance + df['Amount'].sum(),
                "period": f"{min_date} - {max_date}",
                "operations_count": len(df)
            }
            
        if df.empty:
            await msg.edit_text("Не удалось обработать транзакции.")
            return
            
        # Сохраняем данные пользователя в FSM
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        transactions_dict = df.to_dict('records')
        session_id = str(uuid.uuid4())
        
        payload = clean_nan({
            "session_id": session_id,
            "transactions": transactions_dict,
            **metrics
        })
        USER_DATA[session_id] = payload
        
        await state.update_data(
            transactions=transactions_dict,
            initial_balance=initial_balance,
            metrics=metrics,
            session_id=session_id
        )
        
        await msg.edit_text(
            "✅ <b>Данные успешно проанализированы!</b>\n\n"
            "Вы можете открыть интерактивный дашборд в Mini App или запросить графики и ИИ-анализ прямо в чат:",
            parse_mode="HTML",
            reply_markup=get_action_keyboard(session_id)
        )
        
    except Exception as e:
        import html
        import traceback
        err_tb = html.escape(traceback.format_exc())
        logging.error(f"Error processing file: {e}", exc_info=True)
        err_msg = f"❌ <b>Произошла ошибка при обработке файла:</b>\n\n<pre>{err_tb[-3500:]}</pre>"
        try:
            await msg.edit_text(err_msg, parse_mode="HTML")
        except Exception:
            await message.answer(err_msg, parse_mode="HTML")

async def send_graph(message: Message, df: pd.DataFrame, graph_type: str, initial_balance: float = 0.0):
    if graph_type == "pie":
        chart = generate_spending_pie_chart(df)
        caption = "📊 **Структура твоих расходов по категориям**"
    elif graph_type == "balance":
        chart = generate_balance_dynamics(df, initial_balance)
        caption = "📈 **Динамика баланса во времени**"
    elif graph_type == "payees_org":
        chart = generate_top_payees_bar_chart(df, "Организация")
        caption = "🏢 **Топ-5 крупнейших платежей организациям**"
    elif graph_type == "payees_person":
        chart = generate_top_payees_bar_chart(df, "Человек")
        caption = "👤 **Топ-5 крупнейших переводов людям**"
    else:
        return
        
    if chart:
        await message.answer_photo(BufferedInputFile(chart.getvalue(), filename=f"{graph_type}.png"), caption=caption, parse_mode="Markdown")
    else:
        await message.answer(f"Недостаточно данных для построения графика: {caption}")

@dp.callback_query(F.data.in_(["show_pie", "show_balance", "show_payees_org", "show_payees_person", "show_advice", "show_all", "goal_setup"]))
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    transactions = data.get('transactions')
    initial_balance = data.get('initial_balance', 0.0)
    metrics = data.get('metrics', {})
    
    if not transactions:
        await callback.answer("Данные не найдены. Пожалуйста, загрузите выписку заново.", show_alert=True)
        return
        
    df = pd.DataFrame(transactions)
    df['Date'] = pd.to_datetime(df['Date'])
    
    action = callback.data
    await callback.answer()
    
    if action == "show_pie":
        await send_graph(callback.message, df, "pie")
    elif action == "show_balance":
        await send_graph(callback.message, df, "balance", initial_balance)
    elif action == "show_payees_org":
        await send_graph(callback.message, df, "payees_org")
    elif action == "show_payees_person":
        await send_graph(callback.message, df, "payees_person")
    elif action == "show_advice":
        msg = await callback.message.answer("🧠 Анализирую ваши привычки и ищу скрытые резервы...")
        advice = generate_financial_advice(df, metrics.get('total_income', 0.0), metrics.get('total_expenses', 0.0))
        await msg.edit_text(f"💡 Ваш финансовый совет:\n\n{advice}")
    elif action == "goal_setup":
        await callback.message.answer(
            "🎯 **На что вы хотите накопить?**\n"
            "Напишите свободным текстом вашу цель, сумму и желаемый срок (если есть). \n"
            "Например: *Хочу купить машину за 2 000 000 руб через год* или *Нужно 50 000 на отпуск*.", 
            parse_mode="Markdown"
        )
        await state.set_state(GoalForm.amount)
    elif action == "show_all":
        await send_graph(callback.message, df, "pie")
        await send_graph(callback.message, df, "balance", initial_balance)
        await send_graph(callback.message, df, "payees_org")
        await send_graph(callback.message, df, "payees_person")
        msg = await callback.message.answer("🧠 Генерирую совет...")
        advice = generate_financial_advice(df, metrics.get('total_income', 0.0), metrics.get('total_expenses', 0.0))
        await msg.edit_text(f"💡 Финансовый совет от ИИ:\n\n{advice}")

@dp.message(GoalForm.amount)
async def process_goal_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    transactions = data.get('transactions')
    metrics = data.get('metrics')
    if not transactions or not metrics:
        await message.answer("Данные выписки не найдены. Загрузите файл заново.")
        await state.set_state(None)
        return
        
    df = pd.DataFrame(transactions)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Считаем количество месяцев для средних значений
    days = (df['Date'].max() - df['Date'].min()).days
    months = max(1.0, days / 30.44)
    
    expenses = df[df['Amount'] < 0].copy()
    expenses['Amount_Abs'] = expenses['Amount'].abs()
    category_sums = expenses.groupby('Category')['Amount_Abs'].sum().to_dict()
    
    msg = await message.answer("🧠 ИИ анализирует ваши расходы, чтобы составить план накопления...")
    
    answer = process_goal_request(message.text, metrics, category_sums, months)
    
    await msg.edit_text(f"🎯 Расчет вашей цели:\n\n{answer}")
    
    # Сбрасываем только состояние, данные остаются
    await state.set_state(None)

async def main():
    threading.Thread(target=run_tunnel, daemon=True).start()
    await start_webapp()
    while True:
        try:
            logging.info("Starting bot polling...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Bot polling crashed due to API error: {e}")
            logging.info("Restarting polling in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())
