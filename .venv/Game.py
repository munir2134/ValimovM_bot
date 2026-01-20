import tkinter as tk
from tkinter import ttk
import yfinance as yf
import ta
from datetime import datetime

# === НАСТРОЙКИ ===
SYMBOL = "GC=F"  # Золото
REFRESH_RATE = 60000  # Обновление каждую минуту (в мс)


# === ЛОГИКА ===
def load_data(interval, period):
    df = yf.download(SYMBOL, interval=interval, period=period, progress=False)
    return df


def calculate_sl_tp(side, price, df_m15):
    # Простой расчет: SL за экстремум последних 3 свечей, TP 1:2
    if side == "BUY":
        sl = df_m15['Low'].tail(5).min()
        risk = price - sl
        tp = price + (risk * 2)
    else:
        sl = df_m15['High'].tail(5).max()
        risk = sl - price
        tp = price - (risk * 2)
    return sl, tp


def update_signal():
    try:
        # 1. Загрузка данных
        h1 = load_data("1h", "60d")
        m15 = load_data("15m", "7d")

        if h1.empty or m15.empty:
            raise ValueError("Нет данных")

        # 2. Индикаторы H1 (Тренд)
        h1["EMA50"] = ta.trend.ema_indicator(h1["Close"], 50)
        h1["EMA200"] = ta.trend.ema_indicator(h1["Close"], 200)
        h1_last = h1.iloc[-1]

        # 3. Индикаторы M15 (Вход)
        m15["EMA50"] = ta.trend.ema_indicator(m15["Close"], 50)
        m15["EMA200"] = ta.trend.ema_indicator(m15["Close"], 200)
        m15["RSI"] = ta.momentum.rsi(m15["Close"], 14)
        last = m15.iloc[-1]

        current_price = last['Close']

        # Обновление UI цен
        price_label.config(text=f"Цена: {current_price:.2f}")
        rsi_label.config(text=f"RSI M15: {last['RSI']:.2f}")

        # 4. Проверка условий
        signal = "NO TRADE"
        color = "#aaaaaa"
        sl_val, tp_val = 0, 0

        # BUY LOGIC
        if h1_last["EMA50"] > h1_last["EMA200"] and last["EMA50"] > last["EMA200"]:
            if 30 < last["RSI"] < 45:
                signal = "BUY"
                color = "#00ff88"
                sl_val, tp_val = calculate_sl_tp("BUY", current_price, m15)

        # SELL LOGIC
        elif h1_last["EMA50"] < h1_last["EMA200"] and last["EMA50"] < last["EMA200"]:
            if 55 < last["RSI"] < 70:
                signal = "SELL"
                color = "#ff4d4d"
                sl_val, tp_val = calculate_sl_tp("SELL", current_price, m15)

        # 5. Вывод результатов
        signal_label.config(text=signal, fg=color)
        if signal != "NO TRADE":
            tp_label.config(text=f"TP: {tp_val:.2f}", fg="#00ff88")
            sl_label.config(text=f"SL: {sl_val:.2f}", fg="#ff4d4d")
        else:
            tp_label.config(text="TP: --", fg="#666666")
            sl_label.config(text="SL: --", fg="#666666")

        time_label.config(text=f"Обновлено: {datetime.now().strftime('%H:%M:%S')}")

    except Exception as e:
        signal_label.config(text="ERROR", fg="orange")
        print(f"Ошибка: {e}")

    # Зацикливание обновления
    root.after(REFRESH_RATE, update_signal)


# === UI ОФОРМЛЕНИЕ ===
root = tk.Tk()
root.title("XAUUSD Scalper Pro")
root.geometry("400x450")
root.configure(bg="#121212")

# Стилизация заголовка
tk.Label(root, text="GOLD INTRADAY BOT", font=("Segoe UI", 16, "bold"), bg="#121212", fg="#FFD700").pack(pady=20)

# Фрейм для данных
info_frame = tk.Frame(root, bg="#121212")
info_frame.pack(pady=5)

price_label = tk.Label(info_frame, text="Цена: --", font=("Segoe UI", 12), bg="#121212", fg="white")
price_label.pack()

rsi_label = tk.Label(info_frame, text="RSI M15: --", font=("Segoe UI", 12), bg="#121212", fg="#bbb")
rsi_label.pack()

# Сигнал
signal_label = tk.Label(root, text="STARTING...", font=("Segoe UI", 40, "bold"), bg="#121212", fg="#aaaaaa")
signal_label.pack(pady=20)

# Риск менеджмент фрейм
risk_frame = tk.Frame(root, bg="#121212")
risk_frame.pack(pady=10)

tp_label = tk.Label(risk_frame, text="TP: --", font=("Segoe UI", 12, "bold"), bg="#121212", fg="#666666")
tp_label.pack(side=tk.LEFT, padx=20)

sl_label = tk.Label(risk_frame, text="SL: --", font=("Segoe UI", 12, "bold"), bg="#121212", fg="#666666")
sl_label.pack(side=tk.LEFT, padx=20)

# Футер
time_label = tk.Label(root, text="Загрузка...", font=("Segoe UI", 9), bg="#121212", fg="#666666")
time_label.pack(side=tk.BOTTOM, pady=20)

# Первый запуск
root.after(1000, update_signal)