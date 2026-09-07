import pandas as pd
import matplotlib.pyplot as plt
import io

# Темная тема и неоновые стили в духе cyberpunk
plt.style.use('dark_background')
try:
    plt.rc('font', family='DejaVu Sans')
except Exception:
    pass

BG_COLOR = '#111116'
TEXT_COLOR = '#ffffff'
ACCENT_COLOR_1 = '#00f3ff' # Cyan
ACCENT_COLOR_2 = '#b026ff' # Purple

plt.rcParams.update({
    'axes.facecolor': BG_COLOR,
    'figure.facecolor': BG_COLOR,
    'text.color': TEXT_COLOR,
    'axes.labelcolor': TEXT_COLOR,
    'xtick.color': TEXT_COLOR,
    'ytick.color': TEXT_COLOR,
    'axes.edgecolor': '#333344',
    'axes.grid': False,
    'axes.spines.top': False,
    'axes.spines.right': False
})

def generate_spending_pie_chart(df: pd.DataFrame) -> io.BytesIO:
    """Генерирует круговую диаграмму трат по категориям."""
    expenses = df[df['Amount'] < 0].copy()
    if expenses.empty:
        return None
    
    expenses['Amount_Abs'] = expenses['Amount'].abs()
    category_sums = expenses.groupby('Category')['Amount_Abs'].sum().sort_values(ascending=False)
    
    if len(category_sums) > 6:
        top_cats = category_sums[:6].copy() # Copy to avoid SettingWithCopyWarning
        other_sum = category_sums[6:].sum()
        top_cats['Другое'] = other_sum
        category_sums = top_cats
        
    plt.figure(figsize=(8, 6))
    colors = ['#b026ff', '#00f3ff', '#ff2a7a', '#00ff7f', '#ffd700', '#ff8c00', '#555555']
    wedges, texts, autotexts = plt.pie(
        category_sums, labels=category_sums.index, autopct='%1.1f%%', 
        startangle=140, colors=colors, textprops={'color': TEXT_COLOR},
        wedgeprops={'edgecolor': BG_COLOR, 'linewidth': 2}
    )
    plt.title('Структура расходов', color=TEXT_COLOR, pad=20, fontsize=14)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

def generate_balance_dynamics(df: pd.DataFrame, initial_balance: float = 0.0) -> io.BytesIO:
    """Генерирует график динамики баланса по дням."""
    if df.empty:
        return None
        
    daily_sums = df.groupby(df['Date'].dt.date)['Amount'].sum().reset_index()
    daily_sums['Date'] = pd.to_datetime(daily_sums['Date'])
    daily_sums = daily_sums.sort_values('Date')
    
    daily_sums['Balance'] = initial_balance + daily_sums['Amount'].cumsum()
    
    plt.figure(figsize=(10, 5))
    
    # Свечение (несколько полупрозрачных линий)
    for lw, alpha in [(6, 0.1), (4, 0.2), (2, 0.5)]:
        plt.plot(daily_sums['Date'], daily_sums['Balance'], color=ACCENT_COLOR_2, linewidth=lw, alpha=alpha)
        
    plt.plot(daily_sums['Date'], daily_sums['Balance'], marker='o', markersize=4, linestyle='-', color=ACCENT_COLOR_1, linewidth=2, markerfacecolor=ACCENT_COLOR_2)
    
    plt.title(f'Динамика баланса (Начальный остаток: {initial_balance:,.2f} ₽)', color=TEXT_COLOR, pad=20, fontsize=14)
    plt.xlabel('Дата', color='#aaaaaa')
    plt.ylabel('Сумма (₽)', color='#aaaaaa')
    
    # Еле заметная сетка
    plt.grid(True, color='#333344', linestyle='--', alpha=0.5)
    
    # Заливка под графиком
    plt.fill_between(daily_sums['Date'], daily_sums['Balance'], color=ACCENT_COLOR_2, alpha=0.1)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

def generate_top_payees_bar_chart(df: pd.DataFrame, payee_type: str) -> io.BytesIO:
    """Генерирует столбчатую диаграмму топ-5 получателей (Человек или Организация)."""
    if 'PayeeType' not in df.columns:
        df['PayeeType'] = 'Организация' # Fallback
        
    expenses = df[(df['Amount'] < 0) & (df['PayeeType'] == payee_type)].copy()
    if expenses.empty:
        return None
        
    expenses['Amount_Abs'] = expenses['Amount'].abs()
    top_payees = expenses.groupby('Description')['Amount_Abs'].sum().sort_values(ascending=False).head(5)
    
    # Сортируем по возрастанию для красивого отображения снизу вверх (горизонтальный барчарт)
    top_payees = top_payees.sort_values(ascending=True)
    
    plt.figure(figsize=(9, 5))
    color = ACCENT_COLOR_1 if payee_type == "Организация" else ACCENT_COLOR_2
    edge = ACCENT_COLOR_2 if payee_type == "Организация" else ACCENT_COLOR_1
    
    bars = plt.barh(top_payees.index, top_payees.values, color=color, edgecolor=edge, linewidth=1.5, alpha=0.8)
    title = 'Топ-5 крупнейших платежей (Организации)' if payee_type == "Организация" else 'Топ-5 крупнейших переводов (Люди)'
    plt.title(title, color=TEXT_COLOR, pad=20, fontsize=14)
    plt.xlabel('Сумма (₽)', color='#aaaaaa')
    
    # Добавляем подписи сумм на графике
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2, f' {width:,.0f} ₽', 
                 va='center', ha='left', fontsize=10, color=color, fontweight='bold')
    
    # Убираем рамки
    plt.gca().spines['bottom'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.xticks([]) # убираем нижнюю шкалу, так как есть подписи
                 
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

def get_top_payees(df: pd.DataFrame) -> str:
    """Возвращает топ-5 получателей платежей в виде текста."""
    return "" # Deprecated, not used directly in current flow
