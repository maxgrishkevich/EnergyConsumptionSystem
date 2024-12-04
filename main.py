import tkinter as tk
from tkinter import ttk
from data_processing import import_csv
from forecasting import run_forecast, plot_forecast, forecast_energy
from reporting import export_csv, export_pdf
from scenario_analysis import run_scenario_analysis
from ui_elements import create_analysis_tab, create_forecasting_tab, create_reporting_tab, create_scenario_analysis_tab
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from tkinter import filedialog, messagebox
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import pandas as pd
from tensorflow.keras.models import load_model
from data_processing import import_csv, apply_filters
import tempfile
import os
from fpdf import FPDF
from statsmodels.tsa.statespace.sarimax import SARIMAX
import openai
from statsmodels.tsa.arima.model import ARIMA


class EnergyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Аналіз та прогнозування енергоспоживання")
        self.geometry("1000x700")
        self.configure(bg="#F0F0F0")

        self.imported_data = None
        self.saved_figures = []
        self.current_analysis_figure = None
        self.current_forecast_figure = None 
        
        # Атрибути для зберігання графіків з кожної вкладки
        self.current_analysis_figure = None
        self.current_forecast_figure = None
        self.current_scenario_figure = None
        
        # Створення вкладок
        self.tab_control = ttk.Notebook(self)
        create_analysis_tab(self)  # Передаємо self для доступу до всіх атрибутів
        create_forecasting_tab(self)  # Передаємо self
        create_reporting_tab(self)  # Передаємо self
        create_scenario_analysis_tab(self)  # Передаємо self

        # Відображення вкладок
        self.tab_control.pack(expand=1, fill="both")

    def on_energy_type_change(self, *args):
        selected_type = self.energy_type_var.get()
        if selected_type == "Світло":
            self.energy_unit = "кВт*год"
        elif selected_type == "Опалення":
            self.energy_unit = "куб.м, м3"
            self.energy_type_var.trace("w", self.on_energy_type_change)
            

    def add_chart_to_report(self, figure, title=""):
        if figure is None:
            messagebox.showerror("Помилка", "Графік не знайдено.")
            return

        # Створюємо унікальний тимчасовий файл для кожного графіка
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            temp_path = tmp_file.name  # Отримуємо шлях до тимчасового файлу
            figure.savefig(temp_path)  # Зберігаємо графік у тимчасовий файл

        # Додаємо графік до списку saved_figures для подальшого експорту
        self.saved_figures.append((temp_path, title))
        messagebox.showinfo("Звіт", f"Графік '{title}' успішно додано до звіту.")


    def apply_filters(self):
        # Застосування фільтрів до даних
        from data_processing import apply_filters

        from_date = self.from_date.get()
        to_date = self.to_date.get()
        energy_type = self.energy_type_var.get()

        if self.imported_data is None:
            messagebox.showwarning("Помилка", "Будь ласка, імпортуйте дані для фільтрування")
            return

        filtered_data = apply_filters(self.imported_data, from_date, to_date, energy_type)
        if filtered_data is not None:
            self.plot_initial_graph(filtered_data, energy_type)


    def import_csv_data(self):
        """
        Метод для імпорту CSV файлу та відображення початкового графіка з урахуванням вибраного типу енергії.
        """
        # Використовуємо функцію import_csv з dataprocessing
        self.imported_data = import_csv()

        if self.imported_data is not None:
            # Отримуємо значення типу енергії з випадаючого меню
            energy_type = self.energy_type_var.get()  # Наприклад, "Світло" або "Опалення"
            
            # Викликаємо метод для побудови графіка з переданим типом енергії
            self.plot_initial_graph(self.imported_data, energy_type)


    def apply_filters(self):
        """
        Метод для застосування фільтрів до даних, з урахуванням введених дат і вибору типу енергії.
        """
        # Отримання вхідних даних з інтерфейсу
        from_date = self.from_date.get()
        to_date = self.to_date.get()
        energy_type = self.energy_type_var.get()

        # Використовуємо функцію apply_filters з dataprocessing
        if self.imported_data is None:
            messagebox.showwarning("Помилка", "Будь ласка, імпортуйте дані для фільтрування")
            return

        # Застосування фільтрів
        filtered_data = apply_filters(self.imported_data, from_date, to_date, energy_type)
        if filtered_data is not None:
            self.plot_initial_graph(filtered_data, energy_type)


    def forecast_data(self):
        self.run_forecast()


    def export_csv_data(self):
        if self.imported_data is not None:
            export_csv(self.imported_data)
        else:
            tk.messagebox.showwarning("Попередження", "Немає даних для експорту.")


    # Функція для аналізу прогнозу через OpenAI API
    def analyze_forecast_with_gpt4(self, forecast_df):
        """
        Використовує OpenAI API для аналізу прогнозу та генерує рекомендації.
        """
        forecast_text = "Ось прогнозовані дані:\n"
        for index, row in forecast_df.iterrows():
            forecast_text += f"{row['ds'].strftime('%Y-%m-%d')}: {row['yhat']:.2f}\n"
            
        # Додаємо більш детальні інструкції для отримання структурованих висновків і рекомендацій
        forecast_text += (
            "\nБудь ласка, зробіть детальний аналіз на основі прогнозованих даних використання енергії."
            " Виконайте наступне:\n"
            "1. Визначте тренди та зміни в прогнозованих даних.\n"
            "2. Поясніть можливі причини змін у споживанні енергії в певні періоди (в тому числі блекаути через війну в Україні).\n"
            "3. Надайте рекомендації щодо ефективного планування та зниження енергоспоживання, якщо це можливо (коротко) (в період блекаутів).\n"
            "4. Напишіть висновки щодо загального рівня енергоспоживання і можливих заходів для його контролю для пересічних користувачів (коротко)."
        )

        openai.api_key = "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"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ти енергетичний аналітик, що робить висновки з даних про енергоспоживання."},
                    {"role": "user", "content": forecast_text}
                ],
                max_tokens=1500,
                temperature=0.7,
            )
            
            analysis_text = response['choices'][0]['message']['content'].strip()
            print("GPT-4 Analysis Text:", analysis_text)  # Перевірка
            return analysis_text

        except openai.error.OpenAIError as e:
            print(f"Error accessing OpenAI API: {e}")
            return "Помилка при отриманні рекомендацій з OpenAI API."


    # Функція для додавання тексту у звіт
    def add_text_to_report(self, title, content):
        """
        Додає текстовий блок до звіту з заголовком.
        """
        # Додаємо текстовий блок у список збережених елементів для звіту
        self.saved_figures.append((None, f"{title}\n\n{content}"))


    # Оновлена функція run_forecast з інтеграцією аналізу
    def run_forecast(self):
        """
        Запускає функцію прогнозування з використанням обраної моделі та відображає результат.
        """
        forecast_model = self.forecast_model_var.get()
        try:
            months = int(self.months_entry.get())
        except ValueError:
            messagebox.showerror("Помилка", "Будь ласка, введіть коректне число місяців для прогнозу.")
            return

        if self.imported_data is None or self.imported_data.empty:
            messagebox.showerror("Помилка", "Завантажені дані порожні або не завантажені.")
            return

        # Підготовка даних
        df = self.imported_data.rename(columns={"Дата": "ds", "Споживання": "y"})
        df['ds'] = pd.to_datetime(df['ds'], errors='coerce')

        if df['ds'].isnull().any() or not pd.api.types.is_numeric_dtype(df['y']):
            messagebox.showerror("Помилка", "Дані мають некоректний формат.")
            return

        try:
            forecast_df = None
            if forecast_model == "SARIMA":
                sarima_order = (1, 1, 1)
                seasonal_order = (1, 1, 1, 12)
                model = SARIMAX(df['y'], order=sarima_order, seasonal_order=seasonal_order)
                model_fit = model.fit(disp=False)
                forecast_values = model_fit.forecast(steps=months)
                future_dates = pd.date_range(start=df['ds'].iloc[-1], periods=months + 1, freq='M')[1:]
                forecast_df = pd.DataFrame({"ds": future_dates, "yhat": forecast_values.values})

            elif forecast_model == "ETS":
                model = ExponentialSmoothing(df['y'], trend="add", seasonal="add", seasonal_periods=12)
                model_fit = model.fit()
                forecast_values = model_fit.forecast(steps=months)
                future_dates = pd.date_range(start=df['ds'].iloc[-1], periods=months + 1, freq='M')[1:]
                forecast_df = pd.DataFrame({"ds": future_dates, "yhat": forecast_values.values})

            elif forecast_model == "ARIMA":
                arima_order = (5, 1, 0)  # Параметри ARIMA (p, d, q)
                model = ARIMA(df['y'], order=arima_order)
                model_fit = model.fit()
                forecast_values = model_fit.forecast(steps=months)
                future_dates = pd.date_range(start=df['ds'].iloc[-1], periods=months + 1, freq='M')[1:]
                forecast_df = pd.DataFrame({"ds": future_dates, "yhat": forecast_values.values})

            elif forecast_model == "GRU":
                forecast_df = forecast_energy(self, months)

            if forecast_df is None or forecast_df.empty:
                messagebox.showerror("Помилка", "Не вдалося створити прогноз.")
                return

            self.forecast_df = forecast_df
            self.add_forecasted_expenses_to_report(forecast_df)

            plot_forecast(self, df.reset_index(), forecast_df, forecast_model)

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося виконати прогноз: {e}")


    def export_pdf_report(self):
        """
        Експортує дані та графіки у PDF-файл з поліпшеним стилем.
        """
        pdf = FPDF()
        pdf.add_page()

        # Шрифт для кирилиці
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        
        # Заголовок документа
        pdf.set_font("DejaVu", '', 18)
        pdf.cell(200, 10, txt="Звіт про енергоспоживання", ln=True, align='C')
        pdf.ln(10)
        
        # Основний текст
        for item in self.saved_figures:
            image_path, content = item
            
            if image_path:
                pdf.set_font("DejaVu", '', 14)
                pdf.cell(200, 10, txt=content, ln=True, align='C')
                pdf.image(image_path, x=15, w=180)
                pdf.ln(10)
            else:
                pdf.set_font("DejaVu", '', 12)
                pdf.set_fill_color(240, 240, 240)
                pdf.multi_cell(0, 10, txt=content, border=1, align='L', fill=True)
                pdf.ln(5)

        # Додаємо текст витрат передостаннім
        forecast_expenses_text = self.add_forecasted_expenses_to_report(self.forecast_df)
        pdf.set_font("DejaVu", '', 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.multi_cell(0, 10, txt=forecast_expenses_text, border=1, align='L', fill=True)
        pdf.ln(10)
        
        # Додаємо "Аналіз та рекомендації" останнім
        analysis_text = self.analyze_forecast_with_gpt4(self.forecast_df)
        pdf.set_font("DejaVu", '', 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.multi_cell(0, 10, txt="Аналіз та рекомендації:\n\n" + analysis_text, border=1, align='L', fill=True)
        pdf.ln(10)

        # Збереження PDF
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF файли", "*.pdf")])
        if file_path:
            pdf.output(file_path)
            messagebox.showinfo("Експорт", "Звіт успішно збережено в PDF!")
        else:
            messagebox.showwarning("Скасовано", "Збереження файлу було скасовано.")


    def add_forecasted_expenses_to_report(self, forecast_df):
        """
        Додає прогнозовані витрати на електроенергію або опалення до звіту на основі forecast_df і повертає текст.
        """
        # Визначаємо тип енергії та відповідний тариф
        energy_type = self.energy_type_var.get()
        tariff = 4.32 if energy_type == "Світло" else 7.96
        unit = "кВт∙год" if energy_type == "Світло" else "куб.м"

        # Формуємо текст для витрат
        expenses_text = f"Прогнозовані витрати на {energy_type.lower()}:\n"
        for index, row in forecast_df.iterrows():
            date_str = row['ds'].strftime("%Y-%m-%d")
            consumption = row['yhat']
            expense = consumption * tariff
            expenses_text += f"{date_str}: {consumption:.2f} * {tariff} грн/{unit} = {expense:.2f} грн\n"

        # Додаємо текст до звіту
        return expenses_text  # Повертаємо текст


    def run_scenario_analysis(self):
        try:
            # Перевірка та перетворення введених значень
            price_change = float(self.price_change_entry.get().strip()) if self.price_change_entry.get().strip() else 0
            capacity_change = float(self.capacity_change_entry.get().strip()) if self.capacity_change_entry.get().strip() else 0

            # Читання та обробка введених середніх годин відключень на місяць
            blackout_hours_text = self.blackout_hours_entry.get().strip()
            blackout_hours_monthly = [float(x.strip()) for x in blackout_hours_text.split(',') if x.strip()]


            # Перевірка, чи завантажені дані для прогнозу
            if self.forecast_df is None or self.forecast_df.empty:
                messagebox.showerror("Помилка", "Будь ласка, виконайте прогнозування перед сценарним аналізом.")
                return

            # Переконаємося, що кількість місяців відповідає кількості введених значень
            num_months = self.forecast_df['ds'].dt.to_period('M').nunique()
            if len(blackout_hours_monthly) != num_months:
                messagebox.showerror("Помилка", f"Кількість введених середніх годин ({len(blackout_hours_monthly)}) не відповідає кількості місяців у прогнозі ({num_months}).")
                return

            # Створення списку blackout_hours_list для кожного дня на основі середніх значень
            blackout_hours_list = []
            forecast_months = self.forecast_df['ds'].dt.to_period('M')
            for month, avg_hours in zip(forecast_months.unique(), blackout_hours_monthly):
                days_in_month = self.forecast_df[self.forecast_df['ds'].dt.to_period('M') == month]
                blackout_hours_list.extend([avg_hours] * len(days_in_month))

            print("Розподілені години відключень для кожного дня:", blackout_hours_list)

            # Виконання сценарного аналізу
            scenario_df = run_scenario_analysis(
                app=self,
                forecast_data=self.forecast_df,
                price_change=price_change,
                capacity_change=capacity_change,
                blackout_hours_list=blackout_hours_list,
                result_frame=self.scenario_result_frame
            )

        except ValueError:
            messagebox.showerror("Помилка", "Будь ласка, введіть коректні значення для всіх параметрів.")


    def plot_initial_graph(self, data, energy_type):
        self.current_analysis_figure = None
        # Очищення старих графіків
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        # Перетворюємо 'Дата' на datetime, якщо це ще не зроблено
        data['Дата'] = pd.to_datetime(data['Дата'])
        data = data.set_index('Дата')

        # Якщо частота - кожні 10 хвилин, агрегуємо спочатку до щоденної суми, а потім до місячної суми
        if pd.infer_freq(data.index) == '10T':
            data_daily = data.resample('D').sum()
            data_monthly = data_daily.resample('M').sum().reset_index()
        else:
            data_monthly = data.resample('M').sum().reset_index()

        # Налаштування підпису осі Y залежно від типу енергії
        y_label = "Споживання (кВт*год)" if energy_type == "Світло" else "Споживання (куб.м, м3)"

        # Створення графіка на основі вибраного типу діаграми
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        title = f"Місячне споживання {energy_type.lower()} (сума)"
        self.current_analysis_figure = fig

        # Отримання типу графіка з випадаючого меню
        chart_type = self.chart_type_var.get()

        # Побудова графіка відповідного типу
        if chart_type == "Лінійна діаграма":
            ax.plot(data_monthly["Дата"], data_monthly["Споживання"], marker='o', color='b', label=title)
            ax.set_xlabel("Дата", fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
        elif chart_type == "Стовпчаста діаграма":
            ax.bar(data_monthly["Дата"], data_monthly["Споживання"], color='b', label=title)
            ax.set_xlabel("Дата", fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
        elif chart_type == "Гістограма":
            ax.hist(data_monthly["Споживання"], bins=10, color='b', label=title)
            ax.set_xlabel(y_label, fontsize=12)
            ax.set_ylabel("Частота", fontsize=12)

        # Налаштування заголовку, сітки та легенди
        ax.set_title(title.capitalize(), fontsize=14)
        ax.grid(True)
        ax.legend()

        # Поворот міток дати для зручного відображення, якщо це не гістограма
        if chart_type != "Гістограма":
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)

        # Відображення графіка
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self.current_analysis_figure = fig


if __name__ == "__main__":
    app = EnergyApp()
    app.mainloop()