import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import joblib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

model_path = r'C:\Users\Hp\Desktop\maks\models'

# Завантаження збереженої моделі та масштабувальника для GRU
gru_model = load_model('gru_energy_model_year.keras')
scaler = joblib.load('scaler_year.save')

def forecast_energy(app, months=3, seq_length=144 * 7):
    """
    Прогнозування з використанням навченої моделі GRU для вказаної кількості місяців з інтервалом в 10 хвилин.
    """
    # Перевірка наявності завантажених даних
    if app.imported_data is None:
        messagebox.showerror("Помилка", "Будь ласка, імпортуйте дані для прогнозування.")
        return

    # Перетворення та підготовка даних
    df = app.imported_data.rename(columns={"Дата": "timestamp", "Споживання (кВт*год)": "Споживання"})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    new_data = df[['Споживання']]

    # Масштабування нових даних
    new_data_scaled = scaler.transform(new_data.values)

    # Функція для створення послідовностей
    def create_sequences(data, seq_length):
        x = []
        for i in range(len(data) - seq_length):
            x.append(data[i:i + seq_length])
        return np.array(x)

    # Формування вхідних послідовностей для прогнозу
    x_new = create_sequences(new_data_scaled, seq_length)

    # Прогнозування на нових даних з використанням останньої послідовності
    total_steps = months * 30 * 144  # Загальна кількість кроків для 10-хвилинного інтервалу
    y_pred_scaled = []
    last_sequence = x_new[-1]

    for _ in range(total_steps):
        predicted_value = gru_model.predict(last_sequence.reshape(1, seq_length, 1))
        y_pred_scaled.append(predicted_value[0, 0])
        last_sequence = np.append(last_sequence[1:], predicted_value).reshape(seq_length, 1)

    # Зворотне масштабування для отримання реальних значень
    y_pred = scaler.inverse_transform(np.array(y_pred_scaled).reshape(-1, 1))

    # Формування дат для прогнозу з інтервалом у 10 хвилин
    future_dates = pd.date_range(start=new_data.index[-1] + pd.Timedelta(minutes=10), periods=total_steps, freq='10T')
    forecast_df = pd.DataFrame({"ds": future_dates, "yhat": y_pred.flatten()})
    forecast_df.set_index('ds', inplace=True)

    # Агрегування 10-хвилинних прогнозів по місяцях (сума для кожного місяця)
    forecast_monthly = forecast_df.resample('M').sum().reset_index()

    # Обрізання результату до вказаного числа місяців
    forecast_monthly = forecast_monthly.head(months)
    
    return forecast_monthly






def run_forecast(app):
    """
    Виконує прогноз на основі обраної моделі та відображає його на графіку.
    """
    forecast_model = app.forecast_model_var.get()
    
    # Отримуємо кількість місяців для прогнозу
    try:
        months = int(app.months_entry.get())
    except ValueError:
        messagebox.showerror("Помилка", "Будь ласка, введіть коректне число місяців для прогнозу.")
        return

    # Перевіряємо, чи завантажені дані
    if app.imported_data is None or app.imported_data.empty:
        messagebox.showerror("Помилка", "Завантажені дані порожні або не завантажені.")
        print("app.imported_data:", app.imported_data)
        return
    
    # Перейменування колонок у формат, який очікує модель
    df = app.imported_data.rename(columns={"Дата": "ds", "Споживання": "y"})
    
    # Перетворення дати на формат datetime
    df['ds'] = pd.to_datetime(df['ds'], errors='coerce')
    
    # Перевірка, чи всі значення конвертовані без помилок
    if df['ds'].isnull().any():
        messagebox.showerror("Помилка", "Колонка 'Дата' має некоректні значення дати.")
        print("Некоректні дати у колонці 'ds':", df[df['ds'].isnull()])
        return

    # Перевірка, чи колонка 'y' має тільки числові значення
    if not pd.api.types.is_numeric_dtype(df['y']):
        messagebox.showerror("Помилка", "Колонка 'Споживання' повинна містити тільки числові значення.")
        print("Некоректні значення у колонці 'y':", df['y'])
        return

    try:
        forecast_df = None  # Ініціалізуємо forecast_df перед умовними блоками

        if forecast_model == "SARIMA":
            # Використання SARIMA моделі з сезонністю
            sarima_order = (1, 1, 1)  # значення p, d, q
            seasonal_order = (1, 1, 1, 12)  # значення P, D, Q, s для сезонності на 12 місяців

            model = SARIMAX(df['y'], order=sarima_order, seasonal_order=seasonal_order)
            model_fit = model.fit(disp=False)
            forecast_values = model_fit.forecast(steps=months)
            future_dates = pd.date_range(start=df['ds'].iloc[-1], periods=months + 1, freq='M')[1:]
            forecast_df = pd.DataFrame({"ds": future_dates, "yhat": forecast_values.values})
                  
        elif forecast_model == "ETS":
            model = ExponentialSmoothing(df['y'], trend="add", seasonal="add", seasonal_periods=12)
            model_fit = model.fit()
            forecast_values = model_fit.forecast(steps=months)
            future_dates = pd.date_range(start=df['ds'].iloc[-1], periods=months + 1, freq='ME')[1:]
            forecast_df = pd.DataFrame({"ds": future_dates, "yhat": forecast_values.values})

        elif forecast_model == "ARIMA":
            # Використання ARIMA моделі без сезонності
            arima_order = (1, 1, 1)  # параметри p, d, q для ARIMA
            model = ARIMA(df['y'], order=arima_order)
            model_fit = model.fit()
            forecast_values = model_fit.forecast(steps=months)
            future_dates = pd.date_range(start=df['ds'].iloc[-1], periods=months + 1, freq='M')[1:]
            forecast_df = pd.DataFrame({"ds": future_dates, "yhat": forecast_values.values})

        elif forecast_model == "GRU":
            forecast_df = forecast_energy(app, months)

        # Перевірка, чи forecast_df було успішно створено
        if forecast_df is None or forecast_df.empty:
            messagebox.showerror("Помилка", "Не вдалося створити прогноз. Перевірте налаштування моделі.")
            print("forecast_df порожній або не створений:", forecast_df)
            return

        # Побудова графіка
        plot_forecast(app, df.reset_index(), forecast_df, forecast_model)

        return forecast_df  # Повертаємо дані прогнозу для подальшого аналізу

    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося виконати прогноз: {e}")
        print("Помилка виконання прогнозу:", e)
        return None

def plot_forecast(app, df, forecast_df, model_name):
    # Визначаємо одиницю вимірювання залежно від типу енергії
    energy_type = app.energy_type_var.get()  # Отримуємо вибір типу енергії
    y_label = "Споживання (кВт*год)" if energy_type == "Світло" else "Споживання (куб.м, м3)"

    # Створюємо нову фігуру для прогнозу
    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    ax.plot(df['ds'], df['y'], marker='o', color='b', label="Реальні дані")
    ax.plot(forecast_df['ds'], forecast_df['yhat'], marker='o', color='g', label=f"Прогноз ({model_name})")
    ax.set_title(f"Прогноз енергоспоживання на {len(forecast_df)} місяців ({model_name})", fontsize=14)
    ax.set_xlabel("Дата", fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)  # Оновлення підпису осі Y
    ax.grid(True)
    ax.legend()

    # Очищення старого графіка у forecast_result_frame
    for widget in app.forecast_result_frame.winfo_children():
        widget.destroy()

    # Відображення нового графіка у forecast_result_frame
    canvas = FigureCanvasTkAgg(fig, master=app.forecast_result_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Збереження графіка для подальшого експорту
    app.current_forecast_figure = fig
    return fig  # Повертаємо графік для збереження



