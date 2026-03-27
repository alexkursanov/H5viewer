# H5 Reader

Python приложение для просмотра и анализа HDF5 файлов с данными компьютерного моделирования кардиомиоцитов.

## Возможности

- **Открытие файлов** — поддержка HDF5 файлов (.h5, .hdf5)
- **Просмотр структуры** — дерево групп и datasets
- **Графики** — построение графиков для всех циклов и последнего цикла
- **Зависимости** — расчет характеристик (APD, сила, кальций) и построение графиков зависимостей
- **Интегралы** — расчет интегралов токов кальция
- **Экспорт** — сохранение данных в Excel и графиков в PDF

## Установка

```bash
# Создание виртуального окружения (рекомендуется)
python -m venv venv

# Активация (Linux/Mac)
source venv/bin/activate
# или (Windows)
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Установка pytest для тестов
pip install pytest
```

## Запуск

```bash
python main.py
```

или

```bash
./venv/bin/python main.py
```

## Структура проекта

```
H5reader/
├── main.py                 # Точка входа
├── requirements.txt        # Зависимости
├── README.md              # Этот файл
├── docs/                  # Документация
│   ├── manual.md          # Руководство пользователя
│   └── developer.md       # Руководство разработчика
├── src/
│   ├── core/              # Ядро приложения
│   │   ├── h5_reader.py   # Работа с HDF5 файлами
│   │   └── __init__.py
│   ├── ui/                # Графический интерфейс
│   │   ├── main_window.py # Главное окно
│   │   └── __init__.py
│   └── utils/             # Утилиты
│       ├── analysis.py    # Анализ данных
│       ├── exporter.py   # Экспорт в Excel
│       └── __init__.py
└── tests/                 # Тесты
    ├── test_h5_reader.py
    └── test_analysis.py
```

## Интерфейс

### Вкладки

1. **All Cycles** — графики всех данных
2. **Last Cycle** — графики последнего цикла (до 7 графиков)
3. **Dependencies** — таблица зависимостей характеристик от частоты
4. **Integrals** — интегралы токов кальция

### Меню File → Save Data to XLS

- Save All Cycles — все данные
- Save First Cycle — первый цикл
- Save Last Cycle — последний цикл
- Save Parameters — параметры модели
- Save Vars — первые и последние значения переменных
- Save Charts to XLS — графики в PDF + информация в Excel

## Тесты

```bash
pytest tests/ -v
```

## Требования

- Python 3.8+
- PyQt6 >= 6.5.0
- h5py >= 3.9.0
- numpy >= 1.24.0
- pandas >= 2.0.0
- matplotlib >= 3.7.0
- openpyxl >= 3.1.0
- scipy >= 1.11.0

## Лицензия

MIT