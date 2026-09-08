document.addEventListener('DOMContentLoaded', () => {
  const tabsContainer = document.getElementById('category-tabs');
  const chartTitle = document.getElementById('chart-title');
  const chartContainer = document.getElementById('chart-container');

  // Строго 12 месяцев на оси X
  const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];

  // Демо-данные из макета (используются, если sessionStorage пуст)
  const mockData = {
    'Продукты': [30, 40, 35, 55, 50, 65, 60, 75, 70, 85, 80, 95],
    'Рестораны': [45, 60, 55, 70, 65, 80, 95, 110, 105, 120, 135, 140],
    'Транспорт': [0, 15, 25, 28, 60, 64, 85, 90, 130, 134, 148, 150],
    'Одежда': [10, 15, 80, 25, 20, 90, 35, 30, 110, 45, 80, 130],
    'Цифровые товары': [20, 25, 30, 35, 45, 55, 60, 70, 75, 85, 95, 110]
  };

  // ============================================================
  // 1. ИЗВЛЕЧЕНИЕ ДАННЫХ ИЗ SESSIONSTORAGE И ВЫВОД ТЕКСТА
  // ============================================================
  let rawItems = [];
  const storedRaw = sessionStorage.getItem('analyticsData');

  if (storedRaw) {
    try {
      const savedData = JSON.parse(storedRaw);

      let rJson = savedData.result_json;
      if (typeof rJson === 'string') {
        try { rJson = JSON.parse(rJson); } catch (e) {}
      }

      rawItems = rJson?.items || savedData.items || [];

      renderTopRecipients(rawItems);

      // Вывод текста совета
      const adviceCard = document.querySelector('.ai-advice-card');
      if (adviceCard && savedData.advice_text) {
        const textTarget = adviceCard.querySelector('p') || adviceCard;
        textTarget.textContent = savedData.advice_text;
      }

      // Вывод ответа на вопрос
      const textCard = document.getElementById('blockTextLabel');
      const textTarget = document.getElementById('textLabel');
      if (textCard && textTarget && savedData.result_text) {
        textTarget.textContent = savedData.result_text;
      }
    } catch (err) {
      console.error('Ошибка чтения sessionStorage:', err);
    }
  }

  // ============================================================
  // 2. СУММИРОВАНИЕ РАСХОДОВ ПО 12 МЕСЯЦАМ
  // ============================================================
  const monthlyExpenses = {
    'Продукты': Array(12).fill(0),
    'Рестораны': Array(12).fill(0),
    'Транспорт': Array(12).fill(0),
    'Одежда': Array(12).fill(0),
    'Цифровые товары': Array(12).fill(0)
  };

  // Определение номера месяца (0..11) из "12.08.2026" или "2026-08-12"
  function getMonthIndex(dateStr) {
    if (!dateStr || typeof dateStr !== 'string') return null;

    // Формат с точками: "12.08.2026"
    if (dateStr.includes('.')) {
      const parts = dateStr.trim().split('.');
      if (parts.length >= 2) {
        const m = parseInt(parts[1], 10);
        if (!isNaN(m) && m >= 1 && m <= 12) return m - 1;
      }
    }

    // Формат с дефисом: "2026-08-12"
    if (dateStr.includes('-')) {
      const parts = dateStr.trim().split('-');
      if (parts.length >= 2) {
        const m = parseInt(parts[1], 10);
        if (!isNaN(m) && m >= 1 && m <= 12) return m - 1;
      }
    }

    return null;
  }

  // Сопоставление категорий банка с вашими кнопками
  function mapCategory(rawCat) {
    if (!rawCat) return null;
    const cat = rawCat.toLowerCase().trim();

    if (cat.includes('супермаркет') || cat.includes('продукт')) return 'Продукты';
    if (cat.includes('ресторан') || cat.includes('кафе') || cat.includes('fastfood') || cat.includes('отдых')) return 'Рестораны';
    if (cat.includes('транспорт') || cat.includes('такси') || cat.includes('авто') || cat.includes('метро')) return 'Транспорт';
    if (cat.includes('одежд') || cat.includes('обув')) return 'Одежда';
    if (cat.includes('цифр') || cat.includes('подписк') || cat.includes('digital') || cat.includes('связь') || cat.includes('Wildber') || cat.includes('Ozon') || cat.includes('Онлайн') || cat.includes('VK')) return 'Цифровые товары';

    for (const key of Object.keys(monthlyExpenses)) {
      if (key.toLowerCase() === cat) return key;
    }
    return null;
  }

  // Суммируем чеки по месяцам
  let hasRealData = false;

  rawItems.forEach(item => {
    const targetCategory = mapCategory(item.category);
    const amount = Math.abs(parseFloat(item.amount)) || 0;
    const monthIdx = getMonthIndex(item.date);

    if (targetCategory && monthIdx !== null && monthlyExpenses[targetCategory]) {
      monthlyExpenses[targetCategory][monthIdx] = Math.round(
        (monthlyExpenses[targetCategory][monthIdx] + amount) * 100
      ) / 100;
      hasRealData = true;
    }
  });

  const activeDataSource = hasRealData ? monthlyExpenses : mockData;

  // ============================================================
  // 3. ИНИЦИАЛИЗАЦИЯ APEXCHARTS
  // ============================================================
  let chart = null;

  if (typeof ApexCharts === 'undefined') return;
  if (!chartContainer) return;

  const activeBtn = tabsContainer ? tabsContainer.querySelector('.tab-btn.active') : null;
  const initialCategory = activeBtn?.dataset.category || 'Продукты';
  const initialData = activeDataSource[initialCategory] || Array(12).fill(0);

  const chartOptions = {
    series: [{
      name: initialCategory,
      data: initialData
    }],
    chart: {
      type: 'area',
      height: 380,
      width: '100%',
      background: 'transparent',
      toolbar: { show: false },
      animations: {
        enabled: true,
        easing: 'easeinout',
        speed: 450
      }
    },
    markers: {
      size: 4,
      strokeColors: '#18181b',
      strokeWidth: 2,
      hover: { size: 6 }
    },
    theme: { mode: 'dark' },
    stroke: {
      curve: 'smooth',
      width: 1.88
    },
    fill: {
      type: 'gradient',
      gradient: {
        type: 'horizontal',
        colorStops: [
          { offset: 0, color: '#8929FF', opacity: 0.45 },
          { offset: 50, color: '#4B6FFD', opacity: 0.25 },
          { offset: 100, color: '#27DFFF', opacity: 0.45 }
        ]
      }
    },
    grid: {
      borderColor: 'rgba(255, 255, 255, 0.08)',
      yaxis: { lines: { show: true } },
      xaxis: { lines: { show: false } }
    },
    xaxis: {
      categories: months, // Всегда Янв - Дек
      labels: { style: { colors: '#71717a', fontSize: '13px' } },
      axisBorder: { show: false },
      axisTicks: { show: false }
    },
    yaxis: {
      labels: {
        style: { colors: '#71717a', fontSize: '13px' },
        formatter: (val) => `${Math.round(val)} ₽`
      }
    },
    tooltip: {
      theme: 'dark',
      y: { formatter: (val) => `${val} ₽` }
    },
    dataLabels: { enabled: false }
  };

  chart = new ApexCharts(chartContainer, chartOptions);
  chart.render();

  // ============================================================
  // 4. ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК
  // ============================================================
  function onCategoryChange(category) {
    if (!chart) return;

    const data = activeDataSource[category] || Array(12).fill(0);

    chart.updateSeries([{
      name: category,
      data: data
    }]);
  }

  if (tabsContainer) {
    tabsContainer.addEventListener('click', (event) => {
      const button = event.target.closest('.tab-btn');
      if (!button || button.classList.contains('active')) return;

      tabsContainer.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');

      if (chartTitle && button.dataset.title) {
        chartTitle.textContent = button.dataset.title;
      }

      const selectedCategory = button.dataset.category || 'Продукты';
      onCategoryChange(selectedCategory);
    });
  }
});


// ============================================================
// ФУНКЦИЯ ФОРМИРОВАНИЯ ТОП-5 ПОЛУЧАТЕЛЕЙ ПЕРЕВОДОВ
// ============================================================
function renderTopRecipients(items) {
  const listContainer = document.getElementById('merchants-list');
  if (!listContainer) return;

  const recipientsMap = {};

  items.forEach(item => {
    const cat = (item.category || '').toLowerCase();
    const desc = (item.description || '').toLowerCase();

    // Проверяем наличие "перевод" или "сбп"
    const isTransfer = cat.includes('перевод') || cat.includes('сбп') || 
                       desc.includes('перевод') || desc.includes('сбп');

    if (isTransfer) {
      // Имя получателя берем из описания (или категории, если описания нет)
      const recipientName = (item.description || item.category || 'Неизвестный получатель').trim();
      const amount = Math.abs(parseFloat(item.amount)) || 0;

      // Суммируем повторные переводы одному адресату
      recipientsMap[recipientName] = (recipientsMap[recipientName] || 0) + amount;
    }
  });

  // Преобразуем в массив, сортируем по убыванию суммы и берем первые 5
  const topRecipients = Object.entries(recipientsMap)
    .map(([name, total]) => ({
      name,
      total: Math.round(total)
    }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 5);

  // Если переводов нет вообще
  if (topRecipients.length === 0) {
    listContainer.innerHTML = `
      <li class="merchant-item">
        <span class="merchant-name">Переводов не найдено</span>
        <span class="price-pill">0 ₽</span>
      </li>
    `;
    return;
  }

  // Рендерим HTML для списка
  listContainer.innerHTML = topRecipients
    .map((recipient, index) => `
      <li class="merchant-item">
        <span class="merchant-name">${index + 1}. ${recipient.name}</span>
        <span class="price-pill">${recipient.total.toLocaleString('ru-RU')} ₽</span>
      </li>
    `)
    .join('');
}