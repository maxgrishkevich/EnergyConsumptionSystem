import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

def run_scenario_analysis(app, forecast_data, price_change, capacity_change, blackout_hours_list, result_frame):
    """
    Функція для виконання сценарного аналізу з урахуванням одиниць вимірювання і різних годин відключень для кожного дня.
    """
    # Визначаємо одиницю вимірювання залежно від типу енергії
    energy_type = app.energy_type_var.get()  # Отримуємо тип енергії
    y_label = "Споживання (кВт)" if energy_type == "Світло" else "Споживання (куб.м)"

    # Копія прогнозованих даних для застосування змін у сценарному аналізі
    adjusted_price_data = forecast_data.copy()
    adjusted_price_data['yhat'] *= (1 - price_change / 100)
    
    adjusted_capacity_data = forecast_data.copy()
    adjusted_capacity_data['yhat'] *= (1 + capacity_change / 100)
    
    adjusted_peak_data = forecast_data.copy()
    adjusted_peak_data['blackout_hours'] = blackout_hours_list
    adjusted_peak_data['peak_reduction_factor'] = 1 - adjusted_peak_data['blackout_hours'] / 24
    adjusted_peak_data['adjusted_yhat'] = adjusted_peak_data['yhat'] * adjusted_peak_data['peak_reduction_factor']

    # Очищення старих графіків
    for widget in result_frame.winfo_children():
        widget.destroy()

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6), dpi=100)
    fig.tight_layout(pad=5)

    date_format = mdates.DateFormatter('%Y-%m-%d')
    locator = mdates.WeekdayLocator(interval=3)

    ax1.plot(forecast_data["ds"], forecast_data["yhat"], marker='o', color='b', label="Прогноз")
    ax1.plot(adjusted_price_data["ds"], adjusted_price_data["yhat"], marker='o', color='r', label="Зміна ціни")
    ax1.set_title("Вплив зміни ціни на енергію", fontsize=10, fontweight='bold')
    ax1.set_xlabel("Дата", fontsize=10)
    ax1.set_ylabel(y_label, fontsize=10)  # Зміна підпису осі Y
    ax1.grid(visible=True, linestyle='--', alpha=0.7)
    ax1.legend()
    ax1.xaxis.set_major_formatter(date_format)
    ax1.xaxis.set_major_locator(locator)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right", fontsize=10)

    ax2.plot(forecast_data["ds"], forecast_data["yhat"], marker='o', color='b', label="Прогноз")
    ax2.plot(adjusted_capacity_data["ds"], adjusted_capacity_data["yhat"], marker='o', color='g', label="Зміна потужності")
    ax2.set_title("Вплив зміни потужностей", fontsize=10, fontweight='bold')
    ax2.set_xlabel("Дата", fontsize=10)
    ax2.set_ylabel(y_label, fontsize=10)  # Зміна підпису осі Y
    ax2.grid(visible=True, linestyle='--', alpha=0.7)
    ax2.legend()
    ax2.xaxis.set_major_formatter(date_format)
    ax2.xaxis.set_major_locator(locator)
    plt.setp(ax2.get_xticklabels(), rotation=45, ha="right", fontsize=10)

    ax3.plot(forecast_data["ds"], forecast_data["yhat"], marker='o', color='b', label="Прогноз")
    ax3.plot(adjusted_peak_data["ds"], adjusted_peak_data["adjusted_yhat"], marker='o', color='purple', label="Пікові навантаження з відключеннями")
    ax3.set_title("Вплив відключень (години відключень за день)", fontsize=10, fontweight='bold')
    ax3.set_xlabel("Дата", fontsize=12)
    ax3.set_ylabel(y_label, fontsize=10)  # Зміна підпису осі Y
    ax3.grid(visible=True, linestyle='--', alpha=0.7)
    ax3.legend()
    ax3.xaxis.set_major_formatter(date_format)
    ax3.xaxis.set_major_locator(locator)
    plt.setp(ax3.get_xticklabels(), rotation=45, ha="right", fontsize=10)

    # Відображення графіків у фреймі
    canvas = FigureCanvasTkAgg(fig, master=result_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Збереження графіка у атрибуті додатку для подальшого експорту.
    app.current_scenario_figure = fig
