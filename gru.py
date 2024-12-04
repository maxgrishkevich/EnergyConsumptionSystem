import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
import joblib

# Завантаження набору даних
url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00374/energydata_complete.csv"
data = pd.read_csv(url)

# Використання лише стовпця 'Appliances' (споживання енергії приладами) як цільової змінної
data['date'] = pd.to_datetime(data['date'])
data.set_index('date', inplace=True)
data = data[['Appliances']]

# Масштабування даних
scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(data)

# Функція для формування послідовностей для моделі
def create_sequences(data, seq_length):
    x, y = [], []
    for i in range(len(data) - seq_length):
        x.append(data[i:i + seq_length])
        y.append(data[i + seq_length])
    return np.array(x), np.array(y)

# Налаштування довжини послідовності
seq_length = 24 * 7  # Використання 7 днів даних для послідовностей
x, y = create_sequences(data_scaled, seq_length)

# Розподіл на тренувальний та тестовий набори
train_size = int(len(x) * 0.8)
x_train, x_test = x[:train_size], x[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# Побудова та оптимізація моделі GRU
model = Sequential([
    GRU(100, return_sequences=True, input_shape=(x_train.shape[1], x_train.shape[2])),
    Dropout(0.1),
    GRU(50),
    Dropout(0.1),
    Dense(1)
])

# Компіляція моделі з оптимізатором та налаштуванням швидкості навчання
optimizer = Adam(learning_rate=0.002)
model.compile(optimizer=optimizer, loss='mean_squared_error')

# Навчання моделі з ранньою зупинкою
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
history = model.fit(x_train, y_train, validation_data=(x_test, y_test), epochs=50, batch_size=64, callbacks=[early_stop])

# Збереження моделі та scaler для подальшого використання
model.save("gru_energy_model_year.keras")
scaler_filename = "scaler_year.save"
joblib.dump(scaler, scaler_filename)

print("Модель і scaler збережено.")

# Завантаження моделі для використання в майбутньому
# model = load_model("gru_energy_model_year.keras")
# scaler = joblib.load(scaler_filename)

# Прогнозування на тестовому наборі та обернене масштабування
predictions = model.predict(x_test)
predictions = scaler.inverse_transform(predictions)
y_test_original = scaler.inverse_transform(y_test.reshape(-1, 1))

# Відображення результатів
plt.figure(figsize=(12, 6))
plt.plot(y_test_original, label="Реальні дані")
plt.plot(predictions, label="Прогноз GRU")
plt.legend()
plt.xlabel("Час")
plt.ylabel("Споживання електроенергії (Вт)")
plt.title("Прогноз споживання електроенергії на основі річних даних")
plt.show()
