import pandas as pd
from tkinter import filedialog, messagebox


def import_csv():
    """
    Функція для імпорту CSV файлу, яка автоматично визначає тип споживання
    і перейменовує стовпець споживання в стандартне ім'я "Споживання".
    """
    try:
        file_path = filedialog.askopenfilename(filetypes=[("CSV файли", "*.csv"), ("Всі файли", "*.*")])
        if file_path:
            # Завантаження даних з CSV
            data = pd.read_csv(file_path, delimiter=';', quotechar='"')

            # Діагностика: виводимо назви колонок
            print("Columns in imported data:", data.columns)

            # Перевірка наявності ключових колонок
            if 'Дата' not in data.columns:
                messagebox.showerror("Помилка", "Файл не містить необхідної колонки 'Дата'.")
                return None
            
            # Перевірка та обробка колонки "Дата" з урахуванням можливого часу
            try:
                data['Дата'] = pd.to_datetime(data['Дата'], errors='coerce')  # Автоматичне розпізнавання формату
                data = data.dropna(subset=['Дата'])  # Видалення рядків з некоректними датами
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка при обробці дати: {e}")
                return None

            # Перейменування колонки споживання
            if "Споживання (кВт*год)" in data.columns:
                data = data.rename(columns={"Споживання (кВт*год)": "Споживання"})
            elif "Споживання (куб.м, м3)" in data.columns:
                data = data.rename(columns={"Споживання (куб.м, м3)": "Споживання"})
            else:
                messagebox.showerror("Помилка", "Відсутній стовпець споживання ('Споживання (кВт*год)' або 'Споживання (куб.м, м3)').")
                return None

            # Діагностика: виводимо перші кілька рядків
            print("First rows of imported data:", data.head())

            messagebox.showinfo("Імпорт", "Дані успішно імпортовані з CSV!")
            return data
    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося імпортувати дані з CSV: {e}")
        return None


def apply_filters(data, from_date_str, to_date_str, energy_type):
    """
    Функція для фільтрації даних за датами і типом енергії. Повертає відфільтрований датафрейм.
    
    Parameters:
        data (DataFrame): Імпортовані дані.
        from_date_str (str): Дата початку фільтра (YYYY-MM-DD).
        to_date_str (str): Дата закінчення фільтра (YYYY-MM-DD).
        energy_type (str): Тип енергії для аналізу ("Світло" або "Опалення").
    
    Returns:
        DataFrame: Відфільтровані дані.
    """
    from datetime import datetime

    try:
        # Перевірка наявності даних
        if data is None:
            messagebox.showwarning("Помилка", "Будь ласка, імпортуйте дані для фільтрування")
            return None

        # Конвертування дат
        from_date = pd.to_datetime(from_date_str, errors='coerce') if from_date_str else None
        to_date = pd.to_datetime(to_date_str, errors='coerce') if to_date_str else None

        # Перевірка коректності дат
        if from_date and to_date and from_date > to_date:
            messagebox.showwarning("Помилка", "Дата 'Від' не може бути більшою за дату 'До'")
            return None

        # Фільтрація даних за датами
        filtered_data = data
        if from_date:
            filtered_data = filtered_data[filtered_data['Дата'] >= from_date]
        if to_date:
            filtered_data = filtered_data[filtered_data['Дата'] <= to_date]

        # Додаткова фільтрація за типом енергії
        if "Тип енергії" in filtered_data.columns:
            if energy_type == "Світло":
                filtered_data = filtered_data[filtered_data["Тип енергії"] == "Світло"]
            elif energy_type == "Опалення":
                filtered_data = filtered_data[filtered_data["Тип енергії"] == "Опалення"]

        messagebox.showinfo("Успіх", f"Дані відфільтровані: від {from_date_str} до {to_date_str}")
        return filtered_data

    except ValueError:
        messagebox.showerror("Помилка", "Невірний формат дати. Використовуйте формат YYYY-MM-DD.")
        return None
