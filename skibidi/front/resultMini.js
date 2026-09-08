// balance-chart.js

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('balance-chart-container');

  if (!container || typeof ApexCharts === 'undefined') {
    return;
  }

  // 1. Моковые данные (12 точек под 12 месяцев)
  const defaultData = [0, 15, 25, 28, 60, 68, 88, 92, 130, 133, 148, 150];
  const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];

  // 2. Конфигурация графика
  const options = {
    series: [{
      name: 'Баланс',
      data: defaultData
    }],
    chart: {
      type: 'area',
      height: 280,
      width: '100%',
      background: 'transparent',
      toolbar: { show: false },
      animations: {
        enabled: true,
        easing: 'easeinout',
        speed: 500
      }
    },
    theme: {
      mode: 'dark'
    },
    stroke: {
      curve: 'smooth',
      width: 2.88
    },
    fill: {
      type: 'gradient',
      gradient: {
        type: 'horizontal',
        colorStops: [
          { offset: 0, color: '#27DFFF', opacity: 0.45 },
          { offset: 50, color: '#4B6FFD', opacity: 0.25 },
          { offset: 100, color: '#8929FF', opacity: 0.45 }
        ]
      }
    },
    grid: {
      borderColor: 'rgba(255, 255, 255, 0.08)',
      yaxis: { lines: { show: true } },
      xaxis: { lines: { show: false } }
    },
    xaxis: {
      categories: months,
      labels: {
        style: {
          colors: '#71717a',
          fontSize: '11px' // Слегка уменьшен кегль, чтобы все 12 месяцев свободно помещались в карточке
        }
      },
      axisBorder: { show: false },
      axisTicks: { show: false }
    },
    yaxis: {
      labels: {
        style: {
          colors: '#71717a',
          fontSize: '12px'
        },
        formatter: (val) => `${Math.round(val)}₽`
      }
    },
    tooltip: {
      theme: 'dark',
      y: {
        formatter: (val) => `${val} ₽`
      }
    },
    dataLabels: {
      enabled: false
    }
  };

  // 3. Создание и рендер
  const balanceChart = new ApexCharts(container, options);
  balanceChart.render();

  // 4. Глобальная функция для обновления данных с сервера
  window.updateBalanceChart = function(newData, newCategories) {
    if (newCategories) {
      balanceChart.updateOptions({
        xaxis: { categories: newCategories }
      });
    }

    balanceChart.updateSeries([{
      name: 'Баланс',
      data: newData
    }]);
  };
});