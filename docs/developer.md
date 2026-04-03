# H5 Reader - Руководство разработчика

## Содержание

1. [Архитектура проекта](#архитектура-проекта)
2. [Структура кода](#структура-кода)
3. [API компонентов](#api-компонентов)
4. [Разработка](#разработка)
5. [Тестирование](#тестирование)

---

## Архитектура проекта

```
H5reader/
├── main.py                 # Точка входа
├── requirements.txt        # Зависимости
├── README.md              # Основная документация
├── docs/                  # Документация
│   ├── manual.md          # Руководство пользователя
│   └── developer.md       # Этот файл
├── src/
│   ├── core/              # Ядро приложения
│   │   ├── h5_reader.py   # Работа с HDF5 файлами
│   │   └── __init__.py
│   ├── ui/                # Графический интерфейс
│   │   ├── main_window.py # Главное окно
│   │   ├── tabs.py        # Вкладки интерфейса
│   │   └── __init__.py
│   └── utils/             # Утилиты
│       ├── analysis.py    # Анализ данных
│       ├── exporter.py    # Экспорт в Excel
│       ├── ssh_client.py  # SSH подключение
│       └── __init__.py
└── tests/                 # Тесты
    ├── test_h5_reader.py
    ├── test_analysis.py
    └── test_ui.py
```

---

## Структура кода

### src/core/h5_reader.py

Основной модуль для работы с HDF5 файлами.

**Классы:**

#### `H5File`

Датакласс, представляющий открытый HDF5 файл.

**Атрибуты:**
- `path` (str) — путь к файлу
- `filename` (str) — имя файла
- `fid` (h5py.File) — дескриптор файла
- `groups` (List[str]) — список групп
- `datasets` (Dict[str, List[str]]) — словарь datasets по группам
- `time` (Optional[np.ndarray]) — массив времени
- `cycle` (Optional[float]) — длина цикла (мс)
- `start_stim` (Optional[float]) — время стимула
- `count_cycle` (Optional[int]) — количество циклов
- `Herz` (Optional[float]) — частота (Гц)
- `points_mod` (Optional[int]) — остаток точек

**Свойства:**
- `full_path` — полный путь к файлу

#### `H5Reader`

Класс для управления открытыми файлами.

**Методы:**

```python
def open_file(filepath: str) -> H5File:
    """Открыть HDF5 файл и загрузить параметры"""

def read_dataset(group: str, dataset: str) -> Optional[np.ndarray]:
    """Прочитать весь dataset"""

def read_dataset_slice(group: str, dataset: str, start: int, count: int) -> Optional[np.ndarray]:
    """Прочитать часть dataset"""

def close_file(h5file: H5File):
    """Закрыть файл"""

def close_all():
    """Закрыть все файлы"""
```

### src/ui/tabs.py

Вкладки интерфейса. Содержит классы для каждой вкладки.

#### `MatplotlibCanvas`

Canvas для отображения графиков matplotlib в Qt.

```python
class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=6, height=4, dpi=100):
        # width, height - размер в дюймах
        # dpi - разрешение
```

#### `AllCyclesTab`

Вкладка графиков всех циклов.

**Атрибуты:**
- `canvas` — холст для графиков
- `toolbar` — панель инструментов matplotlib
- `single_mode_btn`, `multiple_mode_btn` — кнопки режима
- `show_stimuli_check` — показ стимулов
- `up_slider`, `down_slider` — слайдеры диапазона X

**Методы:**
- `plot(group, dataset)` — построение графика
- `clear_chart()` — очистка графика
- `update_x_range()` — обновление диапазона X

#### `LastCycleTab`

Вкладка графиков последнего цикла.

**Атрибуты:**
- `selected_list` — список выбранных элементов
- `plot_btn`, `total_clear_btn` — кнопки управления
- `page_label` — метка страницы
- `per_page` — графиков на страницу (6)

**Методы:**
- `add_selection(group, dataset)` — добавление в выбор
- `remove_selected()` — удаление выбранного
- `clear_selection()` — очистка выбора
- `plot()` — построение графиков
- `prev_page()`, `next_page()` — навигация

#### `DependenciesTab`

Вкладка зависимостей характеристик.

**Атрибуты:**
- `table` — таблица данных
- `canvas`, `toolbar` — графики
- `x_axis_combo`, `char_combo` — выбор осей

#### `IntegralsTab`

Вкладка интегралов токов кальция.

**Атрибуты:**
- `table` — таблица данных
- `canvas`, `toolbar` — графики
- `x_axis_combo`, `integrals_combo` — выбор осей

### src/ui/main_window.py

Главное окно приложения на PyQt6.

#### `MainWindow`

**Атрибуты:**
- `h5_reader` — экземпляр H5Reader
- `current_file` — текущий открытый файл
- `files` — список всех открытых файлов
- `all_cycles_tab`, `last_cycle_tab`, `dependencies_tab`, `integrals_tab` — вкладки

**Методы:**
- `setup_ui()` — инициализация интерфейса
- `open_file()` — диалог открытия файла
- `load_file(filepath)` — загрузка файла
- `update_tree()` — обновление дерева структуры

### src/utils/analysis.py

Модуль анализа данных.

#### `DataAnalyzer`

Статические методы для расчета характеристик.

```python
# Расчет характеристик напряжения
DataAnalyzer.calculate_characteristics(data, time, cycle, start_stim=10)
# Результат: {V_max, V_min, V_ampl, tV_max, APD20, APD50, APD90}

# Расчет характеристик силы
DataAnalyzer.calculate_force_characteristics(data, start_stim=10)
# Результат: {FXSE_max, FXSE_min, FXSE_ampl, tFXSE_max, FXSE_D50, ...}

# Расчет характеристик кальция
DataAnalyzer.calculate_calcium_characteristics(data, start_stim=10)
# Результат: {Cai_max, Cai_min, Cai_ampl, tCai_max, Cai_D10, ...}

# Расчет характеристик длины
DataAnalyzer.calculate_length_characteristics(data, start_stim=10)

# Расчет интегралов кальция
DataAnalyzer.calculate_calcium_integrals(data_dict, params, cycle)
# data_dict: {'i_rel': np.ndarray, 'i_leak': np.ndarray, ...}
# params: {'V_jSR': float, 'V_c': float, ...}

# Получить данные последнего цикла
DataAnalyzer.get_last_cycle_data(time, data, cycle, points_mod)
# Результат: (t_shift, data_cycle)
```

### src/utils/exporter.py

Модуль экспорта в Excel.

#### `ExcelExporter`

Статические методы для сохранения данных.

```python
# Сохранить все циклы
ExcelExporter.save_all_cycles(time, data_dict, filename, file_label)

# Сохранить данные цикла
ExcelExporter.save_cycle_data(time, data_dict, characteristics, filename, file_label, cycle_type)

# Сохранить параметры
ExcelExporter.save_parameters(params, filename)

# Сохранить первые и последние значения
ExcelExporter.save_last_vars(first_values, last_values, cycle, count_cycle, Herz, filename)

# Сохранить зависимости
ExcelExporter.save_dependencies(dep_data, filename)

# Сохранить интегралы
ExcelExporter.save_integrals(int_data, filename)
```

### src/utils/ssh_client.py

Модуль SSH подключения.

#### `SSHConnection`

Класс для управления SSH/SFTP соединением.

```python
def connect(host, port, username, password, key_file=None, timeout=30) -> bool:
    """Подключиться к SSH серверу"""

def disconnect():
    """Отключиться"""

def list_directory(path) -> list:
    """Список файлов в директории"""

def list_directory_attr(path) -> list:
    """Список файлов с атрибутами"""

def is_connected() -> bool:
    """Проверить подключение"""
```

#### `SSHDialog`

Диалог настроек SSH подключения.

---

## Разработка

### Настройка окружения

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Установка в режиме разработки
pip install -e .
```

### Запуск в режиме разработки

```bash
python main.py
```

### Стиль кода

Проект следует PEP 8. Используйте линтеры:

```bash
# flake8
flake8 src/ --max-line-length=100

# black (автоформатирование)
black src/
```

---

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Все тесты с покрытием
pytest tests/ --cov=src -v

# Только определенный файл
pytest tests/test_h5_reader.py -v

# С детальным выводом
pytest tests/ -v -s
```

### Структура тестов

Тесты используют pytest с fixtures:

```python
@pytest.fixture
def temp_h5_file():
    """Создает временный HDF5 файл для тестов"""
    # Создание файла
    yield temp_path
    # Очистка
    os.unlink(temp_path)

@pytest.fixture
def h5_reader():
    """Создает экземпляр H5Reader"""
    return H5Reader()
```

### Добавление новых тестов

1. Создайте файл `tests/test_<module>.py`
2. Добавьте fixtures в conftest.py (или используйте существующие)
3. Напишите тестовые функции

```python
class TestNewFeature:
    def test_something(self, h5_reader, temp_h5_file):
        # Arrange
        h5file = h5_reader.open_file(temp_h5_file)
        
        # Act
        result = h5_reader.read_dataset('group', 'dataset')
        
        # Assert
        assert result is not None
```

---

## TODO

- [x] Рефакторинг main_window - выделение табов
- [x] Логирование
- [x] Обработка ошибок
- [x] Документация
- [ ] Drag & Drop файлов
- [ ] Поиск в tree
- [ ] Сохранение настроек
- [ ] Пресеты графиков
