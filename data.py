import pandas as pd
import numpy as np

# Параметри для генерації даних
start_date = "2024-01-01 00:00:00"  # Початкова дата для тестового набору
end_date = "2025-01-10 23:50:00"    # Кінцева дата (приблизно 10 днів для тестування)
freq = "10T"  # Частота записів кожні 10 хвилин

# Генерація часових міток з кроком у 10 хвилин
date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

# Генерація випадкових значень для споживання енергії (Вт)
np.random.seed(42)  # Фіксуємо seed для відтворюваності
consumption_values = np.random.uniform(low=0, high=5, size=len(date_range))

# Створення DataFrame
test_data = pd.DataFrame({
    "Дата": date_range,
    "Споживання (Вт)": consumption_values
})

# Збереження у CSV-файл
test_data.to_csv("test_energy_data.csv", sep=";", index=False)
print("Тестовий файл згенеровано як 'test_energy_data.csv'")
