import tkinter as tk
import random

# Инициализация игрового поля
board = [' ' for _ in range(9)]
current_player = 'X'
game_mode = 'PVP'  # Режим игры по умолчанию - игрок против игрока
difficulty = 'easy'  # Уровень сложности по умолчанию


# Функция для отображения игрового поля
def update_board():
    for i in range(9):
        labels[i].config(text=board[i])


# Функция для обработки кликов на клетке
def label_click(index):
    global current_player

    if board[index] == ' ':
        board[index] = current_player
        update_board()

        if check_win(current_player):
            status_label.config(text=f"Игрок {current_player} победил!", fg='green')
            disable_labels()
            return
        elif ' ' not in board:
            status_label.config(text="Ничья!", fg='orange')
            return

        # Смена игрока
        current_player = 'O' if current_player == 'X' else 'X'
        status_label.config(text=f"Ход игрока {current_player}", fg='black')

        # Если ходит компьютер, делаем его ход
        if game_mode == 'PVE' and current_player == 'O':
            if difficulty == 'easy':
                computer_move_easy()
            elif difficulty == 'medium':
                computer_move_medium()
            else:
                computer_move_hard()


def computer_move_easy():
    empty_cells = [i for i, x in enumerate(board) if x == ' ']
    move = random.choice(empty_cells)
    board[move] = 'O'
    update_board()

    if check_win('O'):
        status_label.config(text="Компьютер победил!", fg='red')
        disable_labels()


def computer_move_medium():
    empty_cells = [i for i, x in enumerate(board) if x == ' ']
    # Попробуем сделать выигрышный ход или заблокировать игрока
    for move in empty_cells:
        board[move] = 'O'
        if check_win('O'):
            return
        board[move] = 'X'
        if check_win('X'):
            board[move] = 'O'
            update_board()
            return
        board[move] = ' '

    # Если нет угроза, выбираем случайный ход
    computer_move_easy()


def computer_move_hard():
    move = minimax(0, True)
    board[move] = 'O'
    update_board()

    if check_win('O'):
        status_label.config(text="Компьютер победил!", fg='red')
        disable_labels()


def minimax(depth, is_maximizing):
    if check_win('O'):
        return 1
    if check_win('X'):
        return -1
    if ' ' not in board:
        return 0

    if is_maximizing:
        best = -float('inf')
        best_move = -1
        for i in range(9):
            if board[i] == ' ':
                board[i] = 'O'
                move_score = minimax(depth + 1, False)
                if move_score > best:
                    best = move_score
                    best_move = i
                board[i] = ' '
        return best_move
    else:
        best = float('inf')
        best_move = -1
        for i in range(9):
            if board[i] == ' ':
                board[i] = 'X'
                move_score = minimax(depth + 1, True)
                if move_score < best:
                    best = move_score
                    best_move = i
                board[i] = ' '
        return best_move


def check_win(player):
    win_patterns = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # горизонтали
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # вертикали
        [0, 4, 8], [2, 4, 6]  # диагонали
    ]
    return any(all(board[i] == player for i in pattern) for pattern in win_patterns)


def disable_labels():
    for label in labels:
        label.config(state="disabled")


def reset_game():
    global board, current_player
    board = [' ' for _ in range(9)]
    current_player = 'X'
    status_label.config(text="Ход игрока X", fg='black')
    update_board()


# Функция для изменения режима игры
def change_game_mode(mode):
    global game_mode
    game_mode = mode
    reset_game()


def change_difficulty(level):
    global difficulty
    difficulty = level
    reset_game()


# Основное окно
root = tk.Tk()
root.title("Крестики-нолики")
root.geometry("400x500")
root.config(bg="#f0f0f0")

# Панель управления
frame = tk.Frame(root, bg="#f0f0f0")
frame.pack(pady=20)

# Режим игры
game_mode_label = tk.Label(frame, text="Выберите режим:", font=('Arial', 14), bg="#f0f0f0")
game_mode_label.grid(row=0, column=0, columnspan=2)
pvp_button = tk.Button(frame, text="Игрок против игрока", command=lambda: change_game_mode('PVP'), font=('Arial', 12),
                       width=20, relief="solid", bd=2)
pve_button = tk.Button(frame, text="Игрок против компьютера", command=lambda: change_game_mode('PVE'),
                       font=('Arial', 12), width=20, relief="solid", bd=2)
pvp_button.grid(row=1, column=0, padx=10, pady=5)
pve_button.grid(row=1, column=1, padx=10, pady=5)

# Уровень сложности (для игры с компьютером)
difficulty_label = tk.Label(frame, text="Выберите сложность:", font=('Arial', 14), bg="#f0f0f0")
difficulty_label.grid(row=2, column=0, columnspan=2)
easy_button = tk.Button(frame, text="Легкий", command=lambda: change_difficulty('easy'), font=('Arial', 12), width=10,
                        relief="solid", bd=2)
medium_button = tk.Button(frame, text="Средний", command=lambda: change_difficulty('medium'), font=('Arial', 12),
                          width=10, relief="solid", bd=2)
hard_button = tk.Button(frame, text="Сложный", command=lambda: change_difficulty('hard'), font=('Arial', 12), width=10,
                        relief="solid", bd=2)
easy_button.grid(row=3, column=0, padx=10, pady=5)
medium_button.grid(row=3, column=1, padx=10, pady=5)
hard_button.grid(row=3, column=2, padx=10, pady=5)

# Используем метки для игрового поля
labels = [tk.Label(root, text=' ', width=10, height=3, font=('Arial', 20), relief="solid", anchor="center", bd=5,
                   bg="#f9f9f9") for _ in range(9)]



# Метка для статуса игры
status_label = tk.Label(root, text="Ход игрока X", font=('Arial', 16), bg="#f0f0f0")

# Кнопка для сброса игры
reset_button = tk.Button(root, text="Сбросить игру", width=20, height=2, font=('Arial', 16), command=reset_game,
                         relief="solid", bd=2)


# Запуск приложения
root.mainloop()
abel = tk.Label(root, text="Ход игрока X", font=('Arial', 16))
status_label.grid(row=3, column=0, columnspan=3)

# Кнопка для сброса игры
reset_button = tk.Button(root, text="Сбросить игру", width=20, height=2, font=('Arial', 16), command=reset_game)
reset_button.grid(row=4, column=0, columnspan=3, pady=10)

# Запуск приложения
root.mainloop()

