import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from data_processing import import_csv
from forecasting import run_forecast
from tkinter import Button


def create_forecasting_tab(app):
    # Вкладка для прогнозування
    forecasting_tab = ttk.Frame(app.tab_control)
    app.tab_control.add(forecasting_tab, text="Прогнозування")

    # Поле для введення кількості місяців для прогнозу
    months_label = ttk.Label(forecasting_tab, text="Кількість місяців для прогнозу:", font=("Arial", 10, "bold"))
    months_label.grid(row=0, column=0, padx=(20, 10), pady=(20, 5), sticky="w")
    app.months_entry = ttk.Entry(forecasting_tab, width=10, font=("Arial", 10))
    app.months_entry.grid(row=1, column=0, padx=(20, 10), pady=(0, 20), sticky="w")

    # Випадаюче меню для вибору моделі прогнозування
    model_label = ttk.Label(forecasting_tab, text="Виберіть модель прогнозування:", font=("Arial", 10, "bold"))
    model_label.grid(row=2, column=0, padx=(20, 10), pady=(20, 5), sticky="w")
    app.forecast_model_var = tk.StringVar(value="SARIMA")
    model_dropdown = ttk.Combobox(
        forecasting_tab,
        textvariable=app.forecast_model_var,
        values=["SARIMA", "ETS", "GRU","ARIMA"],
        font=("Arial", 10),
        width=20
    )
    model_dropdown.grid(row=3, column=0, padx=(20, 10), pady=(0, 20), sticky="w")

    # Кнопка для запуску прогнозу
    forecast_button = ttk.Button(forecasting_tab, text="Прогнозувати", command=app.run_forecast)
    forecast_button.grid(row=4, column=0, padx=(20, 10), pady=(10, 5), sticky="w")

    # Кнопка для додавання графіка до звіту
    save_chart_button = ttk.Button(
        forecasting_tab,
        text="Додати графік до звіту",
        command=lambda: app.add_chart_to_report(app.current_forecast_figure, "Прогнозований графік")
    )
    save_chart_button.grid(row=5, column=0, padx=(20, 10), pady=(10, 5), sticky="w")  # Додаємо .grid для кнопки



    # Блок з підказками у верхньому правому куті
    tips_frame = ttk.LabelFrame(forecasting_tab, text="Поради", padding=(10, 5))
    tips_frame.grid(row=0, column=1, rowspan=6, padx=(10, 20), pady=(20, 0), sticky="ne")

    # Мінімалістичний текст підказок
    tips_text = """
1. SARIMA: для даних з вираженою сезонністю.
2. ETS: для даних з трендом і сезонністю.
3. GRU : для великих наборів даних і короткострокових залежностей. Дані за кожні 10 хв.
4. ARIMA: для даних без сезонності.
"""
    tk.Label(tips_frame, text=tips_text, justify="left", font=("Arial", 9), wraplength=200).pack(anchor="nw", padx=5, pady=5)

    # Площа для відображення результатів прогнозу
    app.forecast_result_frame = ttk.Frame(forecasting_tab, relief="solid", padding=10)
    app.forecast_result_frame.grid(row=7, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="nsew")

    # Налаштування розтягування колонок
    forecasting_tab.grid_columnconfigure(0, weight=1)
    forecasting_tab.grid_columnconfigure(1, weight=0)  # Права колонка не розтягується
    forecasting_tab.grid_rowconfigure(7, weight=1)

    return forecasting_tab

def create_reporting_tab(app):
    reporting_tab = ttk.Frame(app.tab_control, padding="10")
    app.tab_control.add(reporting_tab, text="Звіти")

    # Заголовок для звітів
    report_label = tk.Label(reporting_tab, text="Звіти про енергоспоживання", font=("Arial", 16, 'bold'), bg="#F0F0F0")
    report_label.pack(pady=10)

    # Фрейм для кнопок експорту
    export_frame = tk.Frame(reporting_tab, bg="#F0F0F0")
    export_frame.pack(pady=10)

    # Кнопка для експорту в PDF
    pdf_button = tk.Button(export_frame, text="Експортувати PDF", command=app.export_pdf_report, bg="#3F51B5", fg="white")
    pdf_button.grid(row=0, column=0, padx=10)

    # Кнопка для експорту в CSV
    csv_button = tk.Button(export_frame, text="Експортувати CSV", command=app.export_csv_data, bg="#FF9800", fg="white")
    csv_button.grid(row=0, column=1, padx=10)

    return reporting_tab

def create_analysis_tab(app):
    # Вкладка для аналізу даних
    analysis_tab = ttk.Frame(app.tab_control, padding="10")
    app.tab_control.add(analysis_tab, text="Перегляд даних")

    analysis_label = tk.Label(analysis_tab, text="Аналіз даних про енергоспоживання", font=("Arial", 16, 'bold'), bg="#F0F0F0")
    analysis_label.pack(pady=10)

    filter_frame = tk.Frame(analysis_tab, bg="#F0F0F0")
    filter_frame.pack(pady=10)

    from_label = tk.Label(filter_frame, text="Від: ", bg="#F0F0F0")
    from_label.grid(row=0, column=0, padx=5)

    app.from_date = tk.Entry(filter_frame)
    app.from_date.grid(row=0, column=1, padx=5)

    to_label = tk.Label(filter_frame, text="До: ", bg="#F0F0F0")
    to_label.grid(row=0, column=2, padx=5)

    app.to_date = tk.Entry(filter_frame)
    app.to_date.grid(row=0, column=3, padx=5)

    # Вибір типу енергії (Світло або Опалення)
    energy_type_label = tk.Label(filter_frame, text="Тип енергії:", bg="#F0F0F0")
    energy_type_label.grid(row=1, column=0, padx=5)

    app.energy_type_var = tk.StringVar()
    app.energy_type_var.set("Світло")  # Значення за замовчуванням

    energy_type_dropdown = ttk.Combobox(filter_frame, textvariable=app.energy_type_var)
    energy_type_dropdown['values'] = ["Світло", "Опалення"]
    energy_type_dropdown.grid(row=1, column=1, padx=5)

    # Кнопка для застосування фільтрів
    apply_button = tk.Button(filter_frame, text="Застосувати фільтри", command=app.apply_filters, bg="#4CAF50", fg="white")
    apply_button.grid(row=0, column=4, padx=10)

    # Кнопка для імпорту CSV
    import_button = tk.Button(filter_frame, text="Імпортувати CSV", command=app.import_csv_data, bg="#FF5722", fg="white")
    import_button.grid(row=0, column=5, padx=10)

    # Вибір типу діаграми
    chart_type_label = tk.Label(filter_frame, text="Тип діаграми:", bg="#F0F0F0")
    chart_type_label.grid(row=2, column=0, padx=5)

    app.chart_type_var = tk.StringVar()
    app.chart_type_var.set("Лінійна діаграма")

    chart_type_dropdown = ttk.Combobox(filter_frame, textvariable=app.chart_type_var)
    chart_type_dropdown['values'] = ["Лінійна діаграма", "Стовпчаста діаграма", "Гістограма"]
    chart_type_dropdown.grid(row=2, column=1, padx=5)

    # Кнопка для додавання графіка до звіту
    save_chart_button = tk.Button(
        filter_frame,
        text="Додати графік до звіту",
        command=lambda: app.add_chart_to_report(app.current_analysis_figure, "Аналіз даних")
    )
    save_chart_button.grid(row=2, column=4, padx=10)  # Додаємо .grid для кнопки

    # Площа для відображення графіка
    app.chart_frame = tk.Frame(analysis_tab, bg="#F0F0F0")
    app.chart_frame.pack(fill="both", expand=True)

    return analysis_tab


def create_scenario_analysis_tab(app):
    scenario_tab = ttk.Frame(app.tab_control, padding="10")
    app.tab_control.add(scenario_tab, text="Сценарний аналіз")

    scenario_label = tk.Label(scenario_tab, text="Сценарний аналіз", font=("Arial", 16, 'bold'), bg="#F0F0F0")
    scenario_label.pack(pady=10)

    # Фрейм для введення сценарних параметрів
    scenario_frame = tk.Frame(scenario_tab, bg="#F0F0F0")
    scenario_frame.pack(pady=10)

    # Поле для зміни ціни
    price_change_label = tk.Label(scenario_frame, text="Зміна ціни на енергію (%): ", bg="#F0F0F0")
    price_change_label.grid(row=0, column=0, padx=5)
    app.price_change_entry = tk.Entry(scenario_frame)
    app.price_change_entry.grid(row=0, column=1, padx=5)

    # Поле для зміни виробничих потужностей
    capacity_change_label = tk.Label(scenario_frame, text="Зміна виробничих потужностей (%): ", bg="#F0F0F0")
    capacity_change_label.grid(row=1, column=0, padx=5)
    app.capacity_change_entry = tk.Entry(scenario_frame)
    app.capacity_change_entry.grid(row=1, column=1, padx=5)

    # Поле для введення годин відключення (пікові навантаження)
    blackout_hours_label = tk.Label(scenario_frame, text="Години відключення світла (пікові навантаження): ", bg="#F0F0F0")
    blackout_hours_label.grid(row=2, column=0, padx=5)
    app.blackout_hours_entry = tk.Entry(scenario_frame)
    app.blackout_hours_entry.grid(row=2, column=1, padx=5)

    # Кнопка для запуску сценарного аналізу
    scenario_button = tk.Button(scenario_frame, text="Аналізувати", command=app.run_scenario_analysis, bg="#FF5722", fg="white")
    scenario_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    # Кнопка для додавання графіка до звіту
    save_scenario_chart_button = tk.Button(
        scenario_frame,
        text="Додати графік до звіту",
        command=lambda: app.add_chart_to_report(app.current_scenario_figure, "Сценарний аналіз")
    )
    save_scenario_chart_button.grid(row=4, column=0, columnspan=2, padx=10, pady=5)  # Додаємо .grid для кнопки

    # Фрейм для відображення результатів аналізу
    app.scenario_result_frame = tk.Frame(scenario_tab, bg="#F0F0F0")
    app.scenario_result_frame.pack(fill="both", expand=True)

    return scenario_tab




