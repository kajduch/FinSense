import pandas as pd
import io
import re
import pdfplumber


def clean_amount(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).replace(' ', '').replace(',', '.')
    val_str = re.sub(r'[^\d\.-]', '', val_str)
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def parse_bank_statement_csv(file_content: bytes) -> pd.DataFrame:
    """Parses a CSV bank statement (Sberbank, Tinkoff, Alfa, etc)."""
    encodings = ['windows-1251', 'utf-8', 'cp866']
    decoded_text = None
    for enc in encodings:
        try:
            decoded_text = file_content.decode(enc)
            break
        except UnicodeDecodeError:
            continue
            
    if not decoded_text:
        raise ValueError("Не удалось декодировать CSV файл.")
        
    lines = decoded_text.strip().split('\n')
    header_idx = 0
    max_delims = 0
    delimiter = ';'
    
    # Ищем строку с заголовками (обычно там слова 'дата', 'сумма', 'описание')
    # или просто строку с максимальным числом разделителей
    for i, line in enumerate(lines[:30]):
        lower_line = line.lower()
        if 'дата' in lower_line and ('сумма' in lower_line or 'описание' in lower_line or 'операция' in lower_line):
            header_idx = i
            delimiter = ';' if ';' in line else ','
            break
        
        # Резервный вариант: ищем строку с максимальным числом колонок
        c_semi = line.count(';')
        c_comma = line.count(',')
        if c_semi > max_delims:
            max_delims = c_semi
            header_idx = i
            delimiter = ';'
        if c_comma > max_delims and c_comma > c_semi:
            max_delims = c_comma
            header_idx = i
            delimiter = ','

    df = pd.read_csv(io.StringIO(decoded_text), sep=delimiter, skiprows=header_idx)
    df.columns = [str(c).strip().lower() for c in df.columns]

    date_col = next((c for c in df.columns if 'дата' in c or 'date' in c), None)
    desc_col = next((c for c in df.columns if 'описание' in c or 'название' in c or 'наименование' in c or 'description' in c or 'операция' in c), None)
    cat_col = next((c for c in df.columns if 'категори' in c or 'category' in c), None)
    amount_col = next((c for c in df.columns if 'сумма' in c or 'amount' in c), None)

    if not date_col and len(df.columns) > 0: date_col = df.columns[0]
    if not desc_col and len(df.columns) > 1: desc_col = df.columns[1]
    if not amount_col and len(df.columns) > 2: amount_col = df.columns[-1]

    if not all([date_col, desc_col, amount_col]):
        raise ValueError("Не удалось определить структуру CSV. Необходимы колонки с датой, описанием и суммой.")

    normalized_df = pd.DataFrame()
    normalized_df['Date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
    normalized_df['Description'] = df[desc_col].astype(str)
    
    if cat_col:
        normalized_df['Category'] = df[cat_col].astype(str)
    else:
        normalized_df['Category'] = 'Неизвестно'
        
    normalized_df['Amount'] = df[amount_col].apply(clean_amount)
    normalized_df = normalized_df.dropna(subset=['Date'])
    
    initial_balance = 0.0
    for line in lines[:header_idx]:
        lower_line = line.lower()
        if 'входящий остаток' in lower_line or 'начальный остаток' in lower_line or 'входящий баланс' in lower_line:
            matches = re.findall(r'[\d\s]+[\.,]\d+', line)
            if matches:
                try:
                    val_str = matches[-1].replace(' ', '').replace(',', '.')
                    initial_balance = float(val_str)
                except ValueError:
                    pass
            break
            
    # Подсчет метрик
    total_income = normalized_df[normalized_df['Amount'] > 0]['Amount'].sum()
    total_expenses = normalized_df[normalized_df['Amount'] < 0]['Amount'].sum()
    
    if not normalized_df.empty:
        min_date = normalized_df['Date'].min().strftime('%d.%m.%Y')
        max_date = normalized_df['Date'].max().strftime('%d.%m.%Y')
        period = f"{min_date} - {max_date}"
    else:
        period = "Неизвестно"
        
    final_balance = initial_balance + normalized_df['Amount'].sum()
    operations_count = len(normalized_df)
    
    metrics = {
        "initial_balance": initial_balance,
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "final_balance": float(final_balance),
        "period": period,
        "operations_count": operations_count
    }
            
    return normalized_df, metrics

def extract_text_from_pdf(file_content: bytes) -> str:
    """Извлекает текст из PDF."""
    text = ""
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text
