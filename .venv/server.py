import tkinter as tk
from tkinter import ttk
import pandas as pd
import requests
import threading
import time
import winsound
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle

# === КОНФИГУРАЦИЯ ===
SYMBOL = "PAXGUSDT"
BG_COLOR = "#050505"
UP_COLOR = "#00ff88"
DOWN_COLOR = "#ff0044"


class UltimateTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("GOLD REAL-TIME TERMINAL v5.0")
        self.root.geometry("1100x850")
        self.root.configure(bg=BG_COLOR)

        self.offset = 0.0
        self.df = None
        self.last_signal = None
        self.is_loading = False

        self.setup_ui()
        # Запуск потока (обновление каждые 0.3 сек для исключения задержки)
        threading.Thread(target=self.fast_loop, daemon=True).start()

    def setup_ui(self):
        # Панель управления
        ctrl = tk.Frame(self.root, bg="#111", pady=10)
        ctrl.pack(fill="x")

        # 1. ВЫБОР МИНУТ
        tk.Label(ctrl, text="ТФ:", bg="#111", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        self.tf_var = tk.StringVar(value="1m")
        self.tf_combo = ttk.Combobox(ctrl, textvariable=self.tf_var, values=["1m", "5m", "15m", "1h"], width=5,
                                     state="readonly")
        self.tf_combo.pack(side=tk.LEFT, padx=5)

        # 2. КНОПКА ОБНОВИТЬ
        tk.Button(ctrl, text="ОБНОВИТЬ", command=self.manual_refresh, bg="#444", fg="white", font=("Arial", 9, "bold"),
                  relief="flat", padx=15).pack(side=tk.LEFT, padx=20)

        # 3. СИНХРОНИЗАЦИЯ (Offset)
        tk.Label(ctrl, text="SYNC:", bg="#111", fg="#888").pack(side=tk.LEFT, padx=10)
        tk.Button(ctrl, text="-", command=lambda: self.adj(-0.1), bg="#222", fg="white", width=3).pack(side=tk.LEFT)
        self.off_lbl = tk.Label(ctrl, text="0.0", bg="#111", fg="yellow", width=6, font=("Consolas", 10))
        self.off_lbl.pack(side=tk.LEFT)
        tk.Button(ctrl, text="+", command=lambda: self.adj(0.1), bg="#222", fg="white", width=3).pack(side=tk.LEFT)

        self.status = tk.Label(ctrl, text="● LIVE DATA", bg="#111", fg="#00ff00", font=("Arial", 10, "bold"))
        self.status.pack(side=tk.RIGHT, padx=20)

        # Блок Цены
        self.price_lbl = tk.Label(self.root, text="---", font=("Consolas", 85, "bold"), bg=BG_COLOR, fg="white")
        self.price_lbl.pack(pady=5)

        self.sig_lbl = tk.Label(self.root, text="SCAN", font=("Arial", 75, "bold"), bg=BG_COLOR, fg="#222")
        self.sig_lbl.pack()

        # График
        self.fig = Figure(figsize=(9, 5), dpi=100, facecolor=BG_COLOR)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

    def adj(self, v):
        self.offset += v
        self.off_lbl.config(text=f"{self.offset:+.1f}")

    def manual_refresh(self):
        self.is_loading = False
        self.status.config(text="RELOADING...", fg="yellow")

    def fast_loop(self):
        while True:
            try:
                tf = self.tf_var.get()
                # Берем свечи + текущую цену (ticker) для исключения задержки свечного графика
                url_klines = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={tf}&limit=50"
                res = requests.get(url_klines, timeout=2).json()

                df = pd.DataFrame(res, columns=['t', 'o', 'h', 'l', 'c', 'v', 'ct', 'qv', 'tr', 'tb', 'tq', 'i'])
                for col in ['o', 'h', 'l', 'c']: df[col] = df[col].astype(float) + self.offset

                # Считаем индикатор EMA
                df['ema'] = df['c'].ewm(span=20, adjust=False).mean()

                self.df = df
                self.root.after(0, self.update_ui)
                time.sleep(0.3)  # Обновление 3 раза в секунду
            except:
                time.sleep(1)

    def update_ui(self):
        if self.df is None: return
        last = self.df.iloc[-1]
        price = last['c']
        ema = last['ema']

        # Логика сигналов
        sig, col = "WAIT", "#222"
        if price > ema + 0.05:
            sig, col = "BUY", UP_COLOR
        elif price < ema - 0.05:
            sig, col = "SELL", DOWN_COLOR

        if sig != self.last_signal and sig != "WAIT":
            winsound.Beep(1000, 100)
            self.last_signal = sig

        self.price_lbl.config(text=f"{price:.2f}")
        self.sig_lbl.config(text=sig, fg=col)
        self.status.config(text="● LIVE", fg="#00ff00")
        self.draw_candles()

    def draw_candles(self):
        self.ax.clear()
        # Рисуем последние 40 свечей
        sub = self.df.tail(40).reset_index()

        for i, row in sub.iterrows():
            color = UP_COLOR if row['c'] >= row['o'] else DOWN_COLOR
            # Фитиль
            self.ax.plot([i, i], [row['l'], row['h']], color=color, linewidth=1)
            # Тело
            rect = Rectangle((i - 0.3, min(row['o'], row['c'])), 0.6, max(abs(row['c'] - row['o']), 0.02),
                             facecolor=color)
            self.ax.add_patch(rect)

        # Линия EMA
        self.ax.plot(sub['ema'], color="#00d4ff", alpha=0.5, linewidth=1)

        self.ax.set_facecolor(BG_COLOR)
        self.ax.grid(color="#222", linestyle="--", alpha=0.3)
        self.ax.tick_params(colors='white', labelsize=8)
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateTerminal(root)
    root.mainloop()