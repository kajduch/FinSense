document.addEventListener('DOMContentLoaded', () => {
  // 1. Достаем сырую строку по ключу
  const storedRaw = sessionStorage.getItem('analyticsData');

  if (storedRaw) {
    try {
      // 2. Превращаем строку обратно в JS-объект
      const savedData = JSON.parse(storedRaw);
      console.log('Данные успешно получены из sessionStorage:', savedData);

      // 3. Достаем нужные поля (items лежит внутри result_json)
      const items = savedData.result_json.items;
      const resultText = savedData.result_text;
      const adviceText = savedData.advice_text;

      console.log('Транзакции:', items);
      console.log('Текст ответа:', resultText);
      console.log('Совет:', adviceText);

      // 4. Выводим текст совета нейросети
      const adviceCard = document.querySelector('.ai-advice-card');
      if (adviceCard && adviceText) {
        const textTarget = adviceCard.querySelector('p') || adviceCard;
        textTarget.textContent = adviceText;
      }

      // 5. Выводим текст ответа
      const textCard = document.getElementById('blockTextLabel');
      const textTarget = document.getElementById('textLabel');
      if (textCard && textTarget && resultText) {
        textTarget.textContent = resultText;
      }

    } catch (err) {
      console.error('Ошибка обработки данных:', err);
    }
  } else {
    console.warn('В sessionStorage пока нет сохраненных данных');
  }
});