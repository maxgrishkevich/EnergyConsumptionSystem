import csv
import os
import tempfile
from tkinter import filedialog, messagebox
from fpdf import FPDF

def export_csv(data):
    """
    Функція для експорту даних у CSV файл.
    
    Parameters:
        data (DataFrame): Імпортовані дані для експорту.
    """
    try:
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV файли", "*.csv"), ("Всі файли", "*.*")])
        if file_path:
            data.to_csv(file_path, index=False, sep=';', quoting=csv.QUOTE_NONNUMERIC)
            messagebox.showinfo("Експорт", "Дані успішно експортовані у CSV!")
    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося експортувати дані у CSV: {e}")


def export_pdf(data, figures):
    """
    Функція для експорту даних та графіків у PDF файл.
    
    Parameters:
        data (DataFrame): Імпортовані дані для додавання у PDF.
        figures (list): Список збережених графіків у вигляді кортежів (figure, title).
    """
    try:
        # Ініціалізація PDF
        pdf = FPDF()
        pdf.add_page()

        # Додавання шрифту для підтримки кирилиці
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        pdf.set_font('DejaVu', '', 12)

        # Заголовок документа
        pdf.set_font("DejaVu", '', 16)
        pdf.cell(200, 10, txt="Звіт про енергоспоживання", ln=True, align='C')
        pdf.ln(10)

        # Додавання таблиці даних CSV
        if data is not None:
            pdf.set_font("DejaVu", '', 12)
            pdf.cell(200, 10, txt="Таблиця даних CSV", ln=True, align='L')
            pdf.ln(5)

            # Заголовки таблиці
            pdf.set_font("DejaVu", '', 10)
            cell_width = 40
            cell_height = 10

            # Додавання заголовків таблиці
            header = list(data.columns)
            for column in header:
                pdf.cell(cell_width, cell_height, column, border=1, align='C', fill=True)
            pdf.ln(cell_height)

            # Додавання рядків таблиці
            for _, row in data.iterrows():
                for value in row:
                    pdf.cell(cell_width, cell_height, str(value), border=1, align='C')
                pdf.ln(cell_height)

        # Додавання графіків
        for figure, title in figures:
            if figure is not None:  # Перевірка, чи графік є дійсним об'єктом Figure
                # Створення унікального тимчасового файлу для кожного графіка
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    chart_path = tmp_file.name
                    figure.savefig(chart_path)
                
                # Додавання заголовка і графіка в PDF
                pdf.ln(10)
                pdf.set_font('DejaVu', '', 14)
                pdf.cell(200, 10, txt=title, ln=True, align='C')
                pdf.image(chart_path, x=10, y=None, w=190)

                # Видалення тимчасового файлу зображення після додавання в PDF
                os.remove(chart_path)
            else:
                messagebox.showwarning("Увага", f"Графік '{title}' не вдалося зберегти, оскільки він не є дійсним об'єктом Figure.")

        # Збереження в PDF
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF файли", "*.pdf"), ("Всі файли", "*.*")])
        if file_path:
            pdf.output(file_path)
            messagebox.showinfo("Експорт", "Звіт успішно збережено в PDF!")
        else:
            messagebox.showwarning("Скасовано", "Збереження файлу було скасовано.")

    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося створити PDF-звіт: {e}")
