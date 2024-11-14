import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, \
    QPushButton, QDialog, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtMultimedia import QSound  # Для звукового сигнала
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QRect

from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import QDir
import re


class TabloWindow(QWidget):

    def __init__(self, home_team, guest_team, home_score, guest_score, period, home_foul_count, guest_foul_count,
                 timer, home_timeout_state, guest_timeout_state):
        super().__init__()
        self.home_team = home_team
        self.guest_team = guest_team
        self.home_score = int(home_score)
        self.guest_score = guest_score
        self.period = period
        self.home_foul_count = home_foul_count
        self.guest_foul_count = guest_foul_count
        self.timer = timer
        self.home_timeout_state = home_timeout_state,  # Состояния тайм-аутов для домашней команды
        self.guest_timeout_state = guest_timeout_state,

        # Настройки окна табло
        self.setWindowTitle("Баскетбольное табло")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: black;")  # Чёрный фон
        #состояние таймаутов
        self.home_timeout_status = [False, False, False]  # Статус тайм-аутов для домашней команды
        self.guest_timeout_status = [False, False, False]
        self.home_timeout_circles = [QLabel("●") for _ in range(3)]  # Кружки для домашней команды
        self.guest_timeout_circles = [QLabel("●") for _ in range(3)]

        # Шрифты
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller-specific temporary folder
            assets_path = os.path.join(sys._MEIPASS, 'assets', 'Moscow2024', 'MOSCOW2024.otf')
        else:
            # Path for running directly in the project
            assets_path = os.path.join('assets', 'Moscow2024', 'MOSCOW2024.otf')

        font_id = QFontDatabase.addApplicationFont(assets_path)
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else 'Arial'
        self.digit_font = QFont(font_family, 72, QFont.Bold)
        self.text_font = QFont("Arial", 32, QFont.Bold)

        self.is_fullscreen = False

        # Основной слой компоновки
        main_layout = QVBoxLayout()

        # ---- 1-я строка: Названия команд и "ПЕРИОД" ----
        top_row = QHBoxLayout()
        self.home_team_label = QLabel(self.home_team)
        self.home_team_label.setAlignment(Qt.AlignCenter)
        self.home_team_label.setFont(self.text_font)
        self.home_team_label.setStyleSheet("color: white;")
        top_row.addWidget(self.home_team_label)

        self.period_text_label = QLabel("ПЕРИОД")
        self.period_text_label.setAlignment(Qt.AlignCenter)
        self.period_text_label.setFont(self.text_font)
        self.period_text_label.setStyleSheet("color: white;")
        top_row.addWidget(self.period_text_label)

        self.guest_team_label = QLabel(self.guest_team)
        self.guest_team_label.setAlignment(Qt.AlignCenter)
        self.guest_team_label.setFont(self.text_font)
        self.guest_team_label.setStyleSheet("color: white;")
        top_row.addWidget(self.guest_team_label)
        main_layout.addLayout(top_row)

        # ---- 2-я строка: Очки команд и счетчик периода ----
        score_row = QHBoxLayout()
        self.home_score_label = QLabel(str(self.home_score))
        self.home_score_label.setAlignment(Qt.AlignCenter)
        self.home_score_label.setFont(self.digit_font)
        self.home_score_label.setStyleSheet("color: red;")
        score_row.addWidget(self.home_score_label)

        self.period_label = QLabel(str(self.period))
        self.period_label.setAlignment(Qt.AlignCenter)
        self.period_label.setFont(self.digit_font)
        self.period_label.setStyleSheet("color: red;")
        score_row.addWidget(self.period_label)

        self.guest_score_label = QLabel(str(self.guest_score))
        self.guest_score_label.setAlignment(Qt.AlignCenter)
        self.guest_score_label.setFont(self.digit_font)
        self.guest_score_label.setStyleSheet("color: red;")
        score_row.addWidget(self.guest_score_label)
        main_layout.addLayout(score_row)

        # ---- 3-я строка: "ФОЛЫ", "ВРЕМЯ", "ФОЛЫ" ----
        middle_row = QHBoxLayout()
        self.home_foul_text_label = QLabel("ФОЛЫ")
        self.home_foul_text_label.setAlignment(Qt.AlignCenter)
        self.home_foul_text_label.setFont(self.text_font)
        self.home_foul_text_label.setStyleSheet("color: white;")
        middle_row.addWidget(self.home_foul_text_label)

        self.time_text_label = QLabel("ВРЕМЯ")
        self.time_text_label.setAlignment(Qt.AlignCenter)
        self.time_text_label.setFont(self.text_font)
        self.time_text_label.setStyleSheet("color: white;")
        middle_row.addWidget(self.time_text_label)

        self.guest_foul_text_label = QLabel("ФОЛЫ")
        self.guest_foul_text_label.setAlignment(Qt.AlignCenter)
        self.guest_foul_text_label.setFont(self.text_font)
        self.guest_foul_text_label.setStyleSheet("color: white;")
        middle_row.addWidget(self.guest_foul_text_label)
        main_layout.addLayout(middle_row)

        # ---- Обновленный 4-й блок: Фолы, таймер и таймауты ----
        bottom_row_with_timeouts = QHBoxLayout()

        # Домашняя команда (фолы и тайм-ауты)
        home_foul_and_timeouts_layout = QVBoxLayout()
        home_foul_and_timeouts_layout.setAlignment(Qt.AlignCenter)

        # Фолы домашней команды
        self.home_foul_label = QLabel(str(self.home_foul_count))
        self.home_foul_label.setAlignment(Qt.AlignCenter)
        self.home_foul_label.setFont(self.digit_font )
        self.home_foul_label.setStyleSheet("color: red;")
        home_foul_and_timeouts_layout.addWidget(self.home_foul_label)

        # Тайм-ауты домашней команды (кружки)
        home_timeouts_layout = QHBoxLayout()
        home_timeouts_layout.setSpacing(15)  # Минимальное расстояние между кружками
        self.home_timeout_circles = []
        for _ in range(3):
            home_circle = QLabel("●")
            home_circle.setAlignment(Qt.AlignCenter)
            home_circle.setFont(self.text_font)
            home_circle.setStyleSheet("color: green;")
            self.home_timeout_circles.append(home_circle)
            home_timeouts_layout.addWidget(home_circle)
        home_foul_and_timeouts_layout.addLayout(home_timeouts_layout)

        # Добавляем вертикальный блок для домашней команды в основную горизонтальную компоновку
        bottom_row_with_timeouts.addLayout(home_foul_and_timeouts_layout)

        # Таймер в центре с выравниванием
        timer_layout = QVBoxLayout()
        timer_layout.setAlignment(Qt.AlignCenter)
        self.timer_label = QLabel(self.timer)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(self.digit_font)
        self.timer_label.setStyleSheet("color: red;")
        timer_layout.addWidget(self.timer_label)
        bottom_row_with_timeouts.addLayout(timer_layout)

        # Гостевая команда (фолы и тайм-ауты)
        guest_foul_and_timeouts_layout = QVBoxLayout()
        guest_foul_and_timeouts_layout.setAlignment(Qt.AlignCenter)

        # Фолы гостевой команды
        self.guest_foul_label = QLabel(str(self.guest_foul_count))
        self.guest_foul_label.setAlignment(Qt.AlignCenter)
        self.guest_foul_label.setFont(self.digit_font)
        self.guest_foul_label.setStyleSheet("color: red;")
        guest_foul_and_timeouts_layout.addWidget(self.guest_foul_label)

        # Тайм-ауты гостевой команды (кружки)
        guest_timeouts_layout = QHBoxLayout()
        guest_timeouts_layout.setSpacing(15)  # Минимальное расстояние между кружками
        self.guest_timeout_circles = []
        for _ in range(3):
            guest_circle = QLabel("●")
            guest_circle.setAlignment(Qt.AlignCenter)
            guest_circle.setFont(self.text_font)
            guest_circle.setStyleSheet("color: green;")
            self.guest_timeout_circles.append(guest_circle)
            guest_timeouts_layout.addWidget(guest_circle)
        guest_foul_and_timeouts_layout.addLayout(guest_timeouts_layout)

        # Добавляем вертикальный блок для гостевой команды в основную горизонтальную компоновку
        bottom_row_with_timeouts.addLayout(guest_foul_and_timeouts_layout)

        # Добавляем строку с фолами, таймером и тайм-аутами в основной слой компоновки
        main_layout.addLayout(bottom_row_with_timeouts)

        # Устанавливаем основной слой компоновки
        self.setLayout(main_layout)

    def resizeEvent(self, event):
        """Адаптация интерфейса при изменении размера окна"""
        # Размеры для миниатюры
        window_width = self.width()
        window_height = self.height()

        font_size = max(min(window_width, window_height) // 10, 24)  # Минимальный размер шрифта 24
        self.digit_font.setPointSize(font_size)
        self.text_font.setPointSize(font_size // 4)

        self.layout().setContentsMargins(10, 10, 10, 10)
        self.layout().setSpacing(10)

        # Обновляем шрифт для всех элементов интерфейса
        self.home_team_label.setFont(self.text_font)
        self.guest_team_label.setFont(self.text_font)
        self.period_text_label.setFont(self.text_font)
        self.time_text_label.setFont(self.text_font)
        self.home_foul_text_label.setFont(self.text_font)
        self.guest_foul_text_label.setFont(self.text_font)

        self.home_score_label.setFont(self.digit_font)
        self.period_label.setFont(self.digit_font)
        self.guest_score_label.setFont(self.digit_font)
        self.home_foul_label.setFont(self.digit_font)
        self.timer_label.setFont(self.digit_font)
        self.guest_foul_label.setFont(self.digit_font)

        self.update()
    def update_display(self, home_team, guest_team, home_score, guest_score, period, home_foul_count, guest_foul_count,
                       timer, home_timeout_state, guest_timeout_state):
        """
        Метод обновляет все данные на табло.
        """
        if not isinstance(home_timeout_state, list):
            home_timeout_state = [False, False, False]
        if not isinstance(guest_timeout_state, list):
            guest_timeout_state = [False, False, False]

        self.home_team_label.setText(home_team)
        self.guest_team_label.setText(guest_team)
        self.home_score_label.setText(str(home_score))
        self.guest_score_label.setText(str(guest_score))
        self.period_label.setText(str(period))
        self.home_foul_label.setText(str(home_foul_count))
        self.guest_foul_label.setText(str(guest_foul_count))
        self.timer_label.setText(timer)

        for i in range(3):
            self.update_timeout_display("home", i)
            self.update_timeout_display("guest", i)
        self.timer_label.setText(timer)

    def toggle_timeout(self, team, timeout_index):
        """Переключение состояния тайм-аута для команды на определенной позиции."""
        if team == "home":
            self.home_timeout_status[timeout_index] = not self.home_timeout_status[timeout_index]
            self.update_timeout_display("home", timeout_index)
        elif team == "guest":
            self.guest_timeout_status[timeout_index] = not self.guest_timeout_status[timeout_index]
            self.update_timeout_display("guest", timeout_index)

    def update_timeout_display(self, team, timeout_index):
        """Обновление цвета кружков на основе текущего состояния тайм-аута."""
        if team == "home":
            if self.home_timeout_status[timeout_index]:
                # Установить красный цвет для активного тайм-аута
                self.home_timeout_circles[timeout_index].setStyleSheet("color: red;")
            else:
                # Вернуть зеленый цвет для неактивного тайм-аута
                self.home_timeout_circles[timeout_index].setStyleSheet("color: green;")
        elif team == "guest":
            if self.guest_timeout_status[timeout_index]:
                self.guest_timeout_circles[timeout_index].setStyleSheet("color: red;")
            else:
                self.guest_timeout_circles[timeout_index].setStyleSheet("color: green;")

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            # Если уже в полноэкранном режиме, переключаем в режим 800x600
            self.showNormal()
            self.setGeometry(100, 100, 800, 600)  # Позиция и размер 800x600
            self.setWindowFlags(Qt.Window)  # Сбрасываем флаг на обычный режим
            self.is_fullscreen = False
        else:
            # Если не в полноэкранном режиме, переключаем в полноэкранный
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.showFullScreen()
            self.is_fullscreen = True
        self.show()

    def keyPressEvent(self, event):
        # Отслеживаем нажатие клавиши ESC
        if event.key() == Qt.Key_Escape:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Устанавливаем заголовок окна
        self.setWindowTitle("Баскетбольное табло")

        # Размеры окна
        self.setGeometry(100, 100, 800, 600)

        # Главный виджет и основной слой компоновки
        main_widget = QWidget()
        main_layout = QVBoxLayout()






        # ---- Названия команд ----
        team_names_layout = QHBoxLayout()

        # Название команды Хозяева
        self.home_team_name = QLineEdit("")
        self.home_team_name.setPlaceholderText("Название команды")
        self.home_team_name.setAlignment(Qt.AlignCenter)  # Центрируем текст
        self.home_team_label = QLabel("Название команды")
        self.home_team_label.setAlignment(Qt.AlignCenter)
        self.home_team_name.textChanged.connect(self.update_label)

        team_names_layout.addWidget(self.home_team_name)

        # Название команды Гости
        self.guest_team_name = QLineEdit("")
        self.guest_team_name.setPlaceholderText("Название команды")
        self.guest_team_name.setAlignment(Qt.AlignCenter)  # Центрируем текст
        team_names_layout.addWidget(self.guest_team_name)
        self.guest_team_label = QLabel("Название команды")
        self.guest_team_label.setAlignment(Qt.AlignCenter)
        self.guest_team_name.textChanged.connect(self.update_guest_team_label)

        # Добавляем блок названий команд в основной слой
        main_layout.addLayout(team_names_layout)

        # ---- Создаем горизонтальную компоновку для счета ----
        score_layout = QHBoxLayout()

        # Блок для счёта команды Хозяева
        home_score_layout = QVBoxLayout()
        home_score_label = QLabel("СЧЁТ")
        self.home_score_value = QLabel("0")  # Начальный счёт
        self.home_score_value.setStyleSheet("font-size: 32px; font-weight: bold;")
        self.home_score_value.setAlignment(Qt.AlignCenter)

        home_score_buttons_layout = QHBoxLayout()
        self.home_add_1 = QPushButton("+1")
        self.home_add_2 = QPushButton("+2")
        self.home_add_3 = QPushButton("+3")

        home_score_buttons_layout.addWidget(self.home_add_1)
        home_score_buttons_layout.addWidget(self.home_add_2)
        home_score_buttons_layout.addWidget(self.home_add_3)

        self.home_minus_1 = QPushButton("-1")
        self.home_reset = QPushButton("Сброс")

        home_score_layout.addWidget(home_score_label, alignment=Qt.AlignCenter)
        home_score_layout.addWidget(self.home_score_value, alignment=Qt.AlignCenter)
        home_score_layout.addLayout(home_score_buttons_layout)
        home_score_layout.addWidget(self.home_minus_1)
        home_score_layout.addWidget(self.home_reset)

        # ---- Период ----
        period_layout = QVBoxLayout()
        self.period_label = QLabel("ПЕРИОД")
        self.period_value = QLabel("1")  # Номер периода по умолчанию
        self.period_value.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.period_value.setAlignment(Qt.AlignCenter)  # Центрируем цифру периода

        # Кнопки для изменения периода
        self.period_plus_button = QPushButton("+1")
        self.period_minus_button = QPushButton("-1")
        self.period_reset_button = QPushButton("Сбросить")  # Кнопка сброса периода

        period_layout.addWidget(self.period_label, alignment=Qt.AlignCenter)
        period_layout.addWidget(self.period_value, alignment=Qt.AlignCenter)
        period_layout.addWidget(self.period_plus_button)
        period_layout.addWidget(self.period_minus_button)
        period_layout.addWidget(self.period_reset_button)  # Добавляем кнопку сброса

        # ---- Блок для счёта команды Гости ----
        guest_score_layout = QVBoxLayout()
        guest_score_label = QLabel("СЧЁТ")
        self.guest_score_value = QLabel("0")  # Начальный счёт
        self.guest_score_value.setStyleSheet("font-size: 32px; font-weight: bold;")
        self.guest_score_value.setAlignment(Qt.AlignCenter)

        guest_score_buttons_layout = QHBoxLayout()
        self.guest_add_1 = QPushButton("+1")
        self.guest_add_2 = QPushButton("+2")
        self.guest_add_3 = QPushButton("+3")

        guest_score_buttons_layout.addWidget(self.guest_add_1)
        guest_score_buttons_layout.addWidget(self.guest_add_2)
        guest_score_buttons_layout.addWidget(self.guest_add_3)

        self.guest_minus_1 = QPushButton("-1")
        self.guest_reset = QPushButton("Сброс")

        guest_score_layout.addWidget(guest_score_label, alignment=Qt.AlignCenter)
        guest_score_layout.addWidget(self.guest_score_value, alignment=Qt.AlignCenter)
        guest_score_layout.addLayout(guest_score_buttons_layout)
        guest_score_layout.addWidget(self.guest_minus_1)
        guest_score_layout.addWidget(self.guest_reset)

        # Добавляем блоки в основную компоновку (счёт хозяев, период и счёт гостей)
        score_layout.addLayout(home_score_layout)
        score_layout.addLayout(period_layout)  # Период теперь между счётами
        score_layout.addLayout(guest_score_layout)

        # Добавляем блок счета команд и период в основной слой
        main_layout.addLayout(score_layout)

        # создаем горизонтальную компановку для таймаутов и фоллов
        second_layout = QHBoxLayout()
        left_timeout_fouls_layout = QVBoxLayout()
        right_timeout_fouls_layout = QVBoxLayout()

        #блок для таймаутов и фоллов левой команды

        left_timeout_layout = QVBoxLayout()

        #таймауты левой команды
        left_timeout_button_layout = QHBoxLayout()
        left_timeout_label = QLabel("ТАЙМАУТЫ")

        self.home_timeout_button1 = QPushButton("Т")
        self.home_timeout_button2 = QPushButton("Т")
        self.home_timeout_button3 = QPushButton("Т")

        left_timeout_button_layout.addWidget(self.home_timeout_button1)
        left_timeout_button_layout.addWidget(self.home_timeout_button2)
        left_timeout_button_layout.addWidget(self.home_timeout_button3)



        #фоллы левой команды
        left_fouls_layout = QVBoxLayout()
        left_fouls_button_layout = QHBoxLayout()
        left_fouls_label = QLabel("ФОЛЫ")
        self.home_foul_count = QLabel("0")  # Начальное количество фолов
        self.home_foul_count.setAlignment(Qt.AlignCenter)

        self.home_foul_plus = QPushButton("+1 Фол")
        self.home_foul_minus = QPushButton("-1 Фол")
        self.home_foul_reset = QPushButton("Сброс фолов")

        left_fouls_button_layout.addWidget(self.home_foul_plus)
        left_fouls_button_layout.addWidget(self.home_foul_minus)
        left_fouls_button_layout.addWidget(self.home_foul_reset)

        left_timeout_layout.addWidget(left_timeout_label, alignment=Qt.AlignCenter)
        left_timeout_layout.addLayout(left_timeout_button_layout)
        left_fouls_layout.addWidget(left_fouls_label, alignment=Qt.AlignCenter)
        left_fouls_layout.addWidget(self.home_foul_count)
        left_fouls_layout.addLayout(left_fouls_button_layout)

        #все что связано с таймером
        timer_layout = QVBoxLayout()
        self.timer_label = QLabel("00:00")  # Начальное значение времени
        self.timer_label.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_description = QLabel("Выбор времени")
        self.timer_description.setAlignment(Qt.AlignCenter)
        # Строка для установки времени
        self.time_input = QLineEdit()

        self.time_input.setAlignment(Qt.AlignCenter)



        # Кнопки управления таймером
        self.start_button = QPushButton("Старт")
        self.stop_button = QPushButton("Стоп")
        self.reset_button = QPushButton("Сброс")


        # Ограничим размер кнопок
        button_width = self.timer_label.sizeHint().width() + 20  # Ширина кнопок чуть больше ширины таймера

        self.time_input.setFixedWidth(button_width)


        # Горизонтальный layout для кнопок времени и таймера
        time_layout = QHBoxLayout()
        time_layout.addWidget(self.time_input)


        # Добавляем отступы для выравнивания и создания пространства
        timer_layout.addWidget(self.timer_description)
        timer_layout.addLayout(time_layout)  # Добавляем горизонтальный layout с кнопками
        timer_layout.addWidget(self.timer_label)  # Таймер
        timer_layout.addWidget(self.start_button)
        timer_layout.addWidget(self.stop_button)
        timer_layout.addWidget(self.reset_button)


        #правая команда
        right_timeout_layout = QVBoxLayout()

        # таймауты правой команды
        right_timeout_button_layout = QHBoxLayout()
        right_timeout_label = QLabel("ТАЙМАУТЫ")
        self.guest_timeout_button1 = QPushButton("Т")
        self.guest_timeout_button2 = QPushButton("Т")
        self.guest_timeout_button3 = QPushButton("Т")

        right_timeout_button_layout.addWidget(self.guest_timeout_button1)
        right_timeout_button_layout.addWidget(self.guest_timeout_button2)
        right_timeout_button_layout.addWidget(self.guest_timeout_button3)

        # фоллы правой команды
        right_fouls_layout = QVBoxLayout()
        right_fouls_button_layout = QHBoxLayout()
        right_fouls_label = QLabel("ФОЛЫ")
        self.guest_foul_count = QLabel("0")  # Начальное количество фолов
        self.guest_foul_count.setAlignment(Qt.AlignCenter)

        self.guest_foul_plus = QPushButton("+1 Фол")
        self.guest_foul_minus = QPushButton("-1 Фол")
        self.guest_foul_reset = QPushButton("Сброс фолов")

        right_fouls_button_layout.addWidget(self.guest_foul_plus)
        right_fouls_button_layout.addWidget(self.guest_foul_minus)
        right_fouls_button_layout.addWidget(self.guest_foul_reset)

        self.home_timeout_state = [False, False, False]  # Начальные состояния таймаутов для домашней команды
        self.guest_timeout_state = [False, False, False]  # Начальные состояния таймаутов для гостевой команды
        self.home_timeout_state = False
        self.guest_timeout_state = False

        right_timeout_layout.addWidget(right_timeout_label, alignment=Qt.AlignCenter)
        right_timeout_layout.addLayout(right_timeout_button_layout)
        right_fouls_layout.addWidget(right_fouls_label, alignment=Qt.AlignCenter)
        right_fouls_layout.addWidget(self.guest_foul_count)
        right_fouls_layout.addLayout(right_fouls_button_layout)

        left_timeout_fouls_layout.addLayout(left_timeout_layout)
        left_timeout_fouls_layout.addLayout(left_fouls_layout)

        right_timeout_fouls_layout.addLayout(right_timeout_layout)
        right_timeout_fouls_layout.addLayout(right_fouls_layout)

        second_layout.addLayout(left_timeout_fouls_layout)
        second_layout.addLayout(timer_layout)
        second_layout.addLayout(right_timeout_fouls_layout)

        # ---- Миниатюра табло и кнопка "Открыть" ----
        thumbnail_layout = QVBoxLayout()
        self.open_button = QPushButton("Открыть")
        self.fullscreen_button = QPushButton("На весь экран")

        thumbnail_layout.setAlignment(Qt.AlignCenter)

        self.mini_tablo = TabloWindow(
            home_team=self.home_team_name.text(),
            guest_team=self.guest_team_name.text(),
            home_score=self.home_score_value.text(),
            guest_score=self.guest_score_value.text(),
            period=self.period_value.text(),
            home_foul_count=self.home_foul_count.text(),
            guest_foul_count=self.guest_foul_count.text(),
            timer=self.timer_label.text(),
            home_timeout_state=self.home_timeout_state,  # Передаем состояния тайм-аутов
            guest_timeout_state=self.guest_timeout_state,


        )

        self.mini_tablo.setFixedSize(600,400)
        thumbnail_layout.addWidget(self.mini_tablo)





        thumbnail_layout.addWidget(self.open_button)
        thumbnail_layout.addWidget(self.fullscreen_button)

        self.open_button.clicked.connect(self.open_scoreboard)
        self.fullscreen_button.clicked.connect(self.open_scoreboard_fullscreen)

        self.tablo_window = TabloWindow(
            home_team=self.home_team_name.text(),
            guest_team=self.guest_team_name.text(),
            home_score=self.home_score_value.text(),
            guest_score=self.guest_score_value.text(),
            period=self.period_value.text(),
            home_foul_count=self.home_foul_count.text(),
            guest_foul_count=self.guest_foul_count.text(),
            timer=self.timer_label.text(),
            home_timeout_state=self.home_timeout_state,  # Передаем состояния тайм-аутов
            guest_timeout_state=self.guest_timeout_state,

        )

        # Переменная для окна миниатюры
        self.tablo_window = None



        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.seconds = 0
        self.minutes = 0

        # Сигнал для звука
        if hasattr(sys, '_MEIPASS'):
            # Путь для упакованного приложения
            sound_path = os.path.join(sys._MEIPASS, 'assets', 'sound', 'alarm.wav')
        else:
            # Путь для работы напрямую из исходной директории
            sound_path = os.path.join('assets', 'sound', 'alarm.wav')

        # Создаём объект звука
        self.sound = QSound(sound_path)


        main_layout.addLayout(second_layout)
        main_layout.addLayout(thumbnail_layout)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)



        # Подключаем кнопки к обработчикам
        self.start_button.clicked.connect(self.set_time_from_input)
        self.start_button.clicked.connect(self.start_timer)
        self.stop_button.clicked.connect(self.stop_timer)
        self.reset_button.clicked.connect(self.reset_timer)

        # Обработчики для кнопок выбора времени


        # Обработчики для кнопок изменения очков и периода
        self.home_add_1.clicked.connect(self.add_home_score_1)
        self.home_add_2.clicked.connect(self.add_home_score_2)
        self.home_add_3.clicked.connect(self.add_home_score_3)
        self.home_minus_1.clicked.connect(self.minus_home_score_1)
        self.home_reset.clicked.connect(self.reset_home_score)

        self.guest_add_1.clicked.connect(self.add_guest_score_1)
        self.guest_add_2.clicked.connect(self.add_guest_score_2)
        self.guest_add_3.clicked.connect(self.add_guest_score_3)
        self.guest_minus_1.clicked.connect(self.minus_guest_score_1)
        self.guest_reset.clicked.connect(self.reset_guest_score)

        self.period_plus_button.clicked.connect(self.increase_period)
        self.period_minus_button.clicked.connect(self.decrease_period)
        self.period_reset_button.clicked.connect(self.reset_period)

        #таймауты
        # Подключение кнопок для переключения состояния тайм-аутов на основном табло и миниатюре
        self.home_timeout_button1.clicked.connect(lambda: self.toggle_timeout('home', 0))
        self.home_timeout_button2.clicked.connect(lambda: self.toggle_timeout('home', 1))
        self.home_timeout_button3.clicked.connect(lambda: self.toggle_timeout('home', 2))
        self.guest_timeout_button1.clicked.connect(lambda: self.toggle_timeout('guest', 0))
        self.guest_timeout_button2.clicked.connect(lambda: self.toggle_timeout('guest', 1))
        self.guest_timeout_button3.clicked.connect(lambda: self.toggle_timeout('guest', 2))

        #фоллы
        self.home_foul_plus.clicked.connect(self.add_home_foul)
        self.home_foul_minus.clicked.connect(self.remove_home_foul)
        self.home_foul_reset.clicked.connect(self.reset_home_fouls)

        self.guest_foul_plus.clicked.connect(self.add_guest_foul)
        self.guest_foul_minus.clicked.connect(self.remove_guest_foul)
        self.guest_foul_reset.clicked.connect(self.reset_guest_fouls)

    def update_thumbnail(self):
        if not isinstance(self.home_timeout_state, list):
            self.home_timeout_state = [False, False, False]  # Устанавливаем значения по умолчанию, если это не список
        if not isinstance(self.guest_timeout_state, list):
            self.guest_timeout_state = [False, False, False]
        self.mini_tablo.update_display(
            home_team=self.home_team_name.text(),
            guest_team=self.guest_team_name.text(),
            home_score=self.home_score_value.text(),
            guest_score=self.guest_score_value.text(),
            period=self.period_value.text(),
            home_foul_count=self.home_foul_count.text(),
            guest_foul_count=self.guest_foul_count.text(),
            timer=self.timer_label.text(),
            home_timeout_state=self.home_timeout_state,  # Передаем состояния тайм-аутов
            guest_timeout_state=self.guest_timeout_state
        )
    def update_scoreboard(self):
        """
        Эта функция обновляет данные на табло.
        """
        if self.tablo_window:
            self.tablo_window.update_display(
                home_team=self.home_team_name.text(),
                guest_team=self.guest_team_name.text(),
                home_score=self.home_score_value.text(),
                guest_score=self.guest_score_value.text(),
                period=self.period_value.text(),
                home_foul_count=self.home_foul_count.text(),
                guest_foul_count=self.guest_foul_count.text(),
                timer=self.timer_label.text(),
                home_timeout_state=self.home_timeout_state,  # Передаем состояния тайм-аутов
                guest_timeout_state=self.guest_timeout_state
            )
    def update_label(self, text):
        self.home_team_label.setText(text)
        self.update_scoreboard()
        self.update_thumbnail()



    def update_guest_team_label(self):
        self.guest_team_label.setText(self.guest_team_name.text())
        self.update_scoreboard()
        self.update_thumbnail()


    # Функции для изменения очков
    def add_home_score_1(self):
        current_score = int(self.home_score_value.text())
        new_home_score = current_score + 1
        self.home_score_value.setText(str(new_home_score))
        self.update_scoreboard()
        self.update_thumbnail()


    def add_home_score_2(self):
        current_score = int(self.home_score_value.text())
        new_home_score = current_score + 2
        self.home_score_value.setText(str(new_home_score))
        self.update_scoreboard()
        self.update_thumbnail()



    def add_home_score_3(self):
        current_score = int(self.home_score_value.text())
        new_home_score = current_score + 3
        self.home_score_value.setText(str(new_home_score))
        self.update_scoreboard()
        self.update_thumbnail()


    def minus_home_score_1(self):
        current_score = int(self.home_score_value.text())
        new_home_score = current_score - 1
        self.home_score_value.setText(str(new_home_score))
        self.update_scoreboard()
        self.update_thumbnail()

    def reset_home_score(self):
        self.home_score_value.setText("0")
        self.update_scoreboard()
        self.update_thumbnail()


    def add_guest_score_1(self):
        current_score = int(self.guest_score_value.text())
        new_guest_score = current_score + 1
        self.guest_score_value.setText(str(new_guest_score))
        self.update_scoreboard()
        self.update_thumbnail()


    def add_guest_score_2(self):
        current_score = int(self.guest_score_value.text())
        new_guest_score = current_score + 2
        self.guest_score_value.setText(str(new_guest_score))
        self.update_scoreboard()
        self.update_thumbnail()

    def add_guest_score_3(self):
        current_score = int(self.guest_score_value.text())
        new_guest_score = current_score + 3
        self.guest_score_value.setText(str(new_guest_score))
        self.update_scoreboard()
        self.update_thumbnail()

    def minus_guest_score_1(self):
        current_score = int(self.guest_score_value.text())
        new_guest_score = current_score - 1
        self.guest_score_value.setText(str(new_guest_score))
        self.update_scoreboard()
        self.update_thumbnail()

    def reset_guest_score(self):
        self.guest_score_value.setText("0")
        self.update_scoreboard()
        self.update_thumbnail()

    # Функции для обновления счёта
    def update_home_score(self, points):
        current_score = int(self.home_score_value.text())
        new_score = max(0, current_score + points)
        self.home_score_value.setText(str(new_score))

    def update_guest_score(self, points):
        current_score = int(self.guest_score_value.text())
        new_score = max(0, current_score + points)
        self.guest_score_value.setText(str(new_score))


    # Функции для изменения периода
    def increase_period(self):
        current_period = int(self.period_value.text())
        new_period = current_period + 1
        self.period_value.setText(str(new_period))
        self.update_scoreboard()
        self.update_thumbnail()


    def decrease_period(self):
        current_period = int(self.period_value.text())
        new_period = current_period - 1
        self.period_value.setText(str(new_period))
        self.update_scoreboard()
        self.update_thumbnail()


    def reset_period(self):
        self.period_value.setText("1")
        self.update_scoreboard()
        self.update_thumbnail()


    # Таймер
    def set_time_from_input(self):
        """Устанавливает таймер на основе времени, введенного в QLineEdit."""
        time_input = self.time_input.text()
        print(f"Input time: {time_input}")

        match = re.match(r"^([0-9]{2}):([0-9]{2})$", time_input)
        if match:
            self.minutes = int(match.group(1))
            self.seconds = int(match.group(2))
            print(f"Time set: {self.minutes:02}:{self.seconds:02}")

            self.timer_label.setText(f"{self.minutes:02}:{self.seconds:02}")
            self.update_scoreboard()
            self.update_thumbnail()
        else:
            print("Invalid time format!")
            self.time_input.setText("введите мм:cc")
            self.timer_label.setText("00:00")
            self.minutes = 0
            self.seconds = 0
            self.update_scoreboard()
            self.update_thumbnail()

    def start_timer(self):
        """Запускает таймер, если он не на нуле."""
        if self.minutes > 0 or self.seconds > 0:
            self.timer.start(1000)  # Таймер обновляется каждую секунду

    def stop_timer(self):
        """Останавливает таймер."""
        self.timer.stop()
        self.update_scoreboard()
        self.update_thumbnail()

    def reset_timer(self):
        """Сбрасывает таймер на 00:00 и останавливает его."""
        self.timer.stop()
        self.minutes = 0
        self.seconds = 0
        self.timer_label.setText("00:00")
        self.update_scoreboard()
        self.update_thumbnail()

    def update_timer(self):
        """Обновляет таймер каждую секунду и синхронизирует табло."""
        if self.minutes == 0 and self.seconds == 0:
            self.timer.stop()
            self.sound.play()
            print("Timer finished!")
            self.update_scoreboard()
            self.update_thumbnail()
            return

        self.seconds -= 1
        if self.seconds < 0:
            self.seconds = 59
            self.minutes -= 1

        self.timer_label.setText(f"{self.minutes:02}:{self.seconds:02}")
        self.update_scoreboard()
        self.update_thumbnail()



    # Функции для изменения фолов
    def add_home_foul(self):
        current_foul = int(self.home_foul_count.text())
        new_home_foul = current_foul + 1
        self.home_foul_count.setText(str(new_home_foul))
        self.update_scoreboard()
        self.update_thumbnail()


    def remove_home_foul(self):
        current_foul = int(self.home_foul_count.text())
        new_home_foul = current_foul - 1
        self.home_foul_count.setText(str(new_home_foul))
        self.update_scoreboard()
        self.update_thumbnail()


    def reset_home_fouls(self):
        self.home_foul_count.setText("0")
        self.update_scoreboard()
        self.update_thumbnail()

    def add_guest_foul(self):
        current_foul = int(self.guest_foul_count.text())
        new_guest_foul = current_foul + 1
        self.guest_foul_count.setText(str(new_guest_foul))
        self.update_scoreboard()
        self.update_thumbnail()


    def remove_guest_foul(self):
        current_foul = int(self.guest_foul_count.text())
        new_guest_foul = current_foul - 1
        self.guest_foul_count.setText(str(new_guest_foul))
        self.update_scoreboard()
        self.update_thumbnail()


    def reset_guest_fouls(self):
        self.guest_foul_count.setText("0")
        self.update_scoreboard()
        self.update_thumbnail()


    # Функции для обновления счётчика фолов
    def update_home_foul(self, count):
        current_fouls = int(self.home_foul_count.text())
        new_fouls = max(0, current_fouls + count)  # Не допускаем значения ниже 0
        self.home_foul_count.setText(str(new_fouls))


    def update_guest_foul(self, count):
        current_fouls = int(self.guest_foul_count.text())
        new_fouls = max(0, current_fouls + count)  # Не допускаем значения ниже 0
        self.guest_foul_count.setText(str(new_fouls))

    def toggle_home_timeout1(self):
        # Переключаем состояние тайм-аута
        self.home_timeout_state[0] = not self.home_timeout_state[0]

        # Обновляем стиль кружка на табло
        if self.home_timeout_state[0]:
            self.home_timeout_circles[0].setStyleSheet("color: red;")  # Тайм-аут красный
        else:
            self.home_timeout_circles[0].setStyleSheet("color: green;")  # Тайм-аут зеленый

        self.update_thumbnail()  # Обновляем мини-табло с новыми состояниями тайм-аутов

    def toggle_home_timeout2(self):
        # Переключаем состояние тайм-аута
        self.home_timeout_state[1] = not self.home_timeout_state[1]

        # Обновляем стиль кружка на табло
        if self.home_timeout_state[1]:
            self.home_timeout_circles[1].setStyleSheet("color: red;")  # Тайм-аут красный
        else:
            self.home_timeout_circles[1].setStyleSheet("color: green;")  # Тайм-аут зеленый

        self.update_thumbnail()  # Обновляем мини-табло с новыми состояниями тайм-аутов

    def toggle_home_timeout3(self):
        # Переключаем состояние тайм-аута
        self.home_timeout_state[2] = not self.home_timeout_state[2]

        # Обновляем стиль кружка на табло
        if self.home_timeout_state[2]:
            self.home_timeout_circles[2].setStyleSheet("color: red;")  # Тайм-аут красный
        else:
            self.home_timeout_circles[2].setStyleSheet("color: green;")  # Тайм-аут зеленый

        self.update_thumbnail()  # Обновляем мини-табло с новыми состояниями тайм-аутов

    def toggle_guest_timeout1(self):
        # Переключаем состояние тайм-аута
        self.guest_timeout_state[0] = not self.guest_timeout_state[0]

        # Обновляем стиль кружка на табло
        if self.guest_timeout_state[0]:
            self.guest_timeout_circles[0].setStyleSheet("color: red;")  # Тайм-аут красный
        else:
            self.guest_timeout_circles[0].setStyleSheet("color: green;")  # Тайм-аут зеленый

        self.update_thumbnail()  # Обновляем мини-табло с новыми состояниями тайм-аутов

    def toggle_guest_timeout2(self):
        # Переключаем состояние тайм-аута
        self.guest_timeout_state[1] = not self.guest_timeout_state[1]

        # Обновляем стиль кружка на табло
        if self.guest_timeout_state[1]:
            self.guest_timeout_circles[1].setStyleSheet("color: red;")  # Тайм-аут красный
        else:
            self.guest_timeout_circles[1].setStyleSheet("color: green;")  # Тайм-аут зеленый

        self.update_thumbnail()  # Обновляем мини-табло с новыми состояниями тайм-аутов

    def toggle_guest_timeout3(self):
        # Переключаем состояние тайм-аута
        self.guest_timeout_state[2] = not self.guest_timeout_state[2]

        # Обновляем стиль кружка на табло
        if self.guest_timeout_state[2]:
            self.guest_timeout_circles[2].setStyleSheet("color: red;")  # Тайм-аут красный
        else:
            self.guest_timeout_circles[2].setStyleSheet("color: green;")  # Тайм-аут зеленый

        self.update_thumbnail()  # Обновляем мини-табло с новыми состояниями тайм-аутов

    def open_scoreboard(self):
        if self.tablo_window is None:
            self.tablo_window = TabloWindow(
                home_team=self.home_team_name.text(),
                guest_team=self.guest_team_name.text(),
                home_score=self.home_score_value.text(),
                guest_score=self.guest_score_value.text(),
                period=self.period_value.text(),
                home_foul_count=0,  # Инициализация счетчика фолов
                guest_foul_count=0,  # Инициализация счетчика фолов
                timer="00:00",
                home_timeout_state=self.home_timeout_state,  # Передаем состояния тайм-аутов
                guest_timeout_state=self.guest_timeout_state
            )
            self.tablo_window.show()

    def toggle_timeout(self, team, index):
        """
        Переключает состояние тайм-аута (кружков) для основной панели и миниатюры.

        :param team: команда ('home' или 'guest')
        :param index: индекс тайм-аута (0, 1 или 2)
        """
        # Обновляем состояние тайм-аута на основном табло
        if self.tablo_window is not None:
            self.tablo_window.toggle_timeout(team, index)

        # Обновляем состояние тайм-аута на миниатюре
        self.mini_tablo.toggle_timeout(team, index)


    def open_scoreboard_fullscreen(self):
        if self.tablo_window is None:
            self.tablo_window = TabloWindow(
                home_team=self.home_team_name.text(),
                guest_team=self.guest_team_name.text(),
                home_score=self.home_score_value.text(),
                guest_score=self.guest_score_value.text(),
                period=self.period_value.text(),
                home_foul_count=0,
                guest_foul_count=0,
                timer="00:00",
                home_timeout_state = self.home_timeout_state,  # Состояния тайм-аутов для домашней команды
                guest_timeout_state = self.guest_timeout_state



            )

        # Если окно еще не полноэкранное, то переводим его в полноэкранный режим
        if not self.tablo_window.isFullScreen():
            # Устанавливаем флаги для полного экрана и удержания окна поверх других
            self.tablo_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.tablo_window.showFullScreen()  # Переводим в полноэкранный режим
        else:
            # Если окно уже полноэкранное, возвращаем его в нормальный режим
            self.tablo_window.setWindowFlags(Qt.Window)
            self.tablo_window.showNormal()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
