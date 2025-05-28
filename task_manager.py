import csv
import os
from datetime import datetime, timedelta, time
import matplotlib.pyplot as plt
from win10toast import ToastNotifier
import sys
#V 0.1.89
class NotificationManager:
    def __init__(self):
        self.enabled = False
        self.toaster = None
        self._initialize()
    
    def _initialize(self):
        try:
            if sys.platform != 'win32':
                return
                
            from win10toast import ToastNotifier
            self.toaster = ToastNotifier()
            self.enabled = True
        except ImportError:
            print("Библиотека win10toast не установлена. Уведомления будут выводиться в консоль.")
        except Exception as e:
            print(f"Системные уведомления недоступны: {str(e)}")
    
    def show(self, title, message, duration=3):
        if self.enabled and self.toaster:
            try:
                self.toaster.show_toast(
                    title,
                    message,
                    duration=duration,
                    threaded=False
                )
                
                time.sleep(duration + 2)
                return True
            except Exception as e:
                print(f"Ошибка уведомления: {str(e)}")
        
        print(f"\n\033[93m[УВЕДОМЛЕНИЕ] {title}: {message}\033[0m\n")
        return False

class Task:
    def __init__(self, title, due_date=None, status="Не начата", progress=0):
        self.title = title
        self.due_date = due_date
        self.status = status
        self.progress = progress
        self.created_date = datetime.now().strftime("%Y-%m-%d")
    
    def update_progress(self, new_progress):
        new_progress = max(0, min(100, new_progress))
        self.progress = new_progress
        if new_progress == 100:
            self.status = "Завершена"
        elif new_progress > 0:
            self.status = "В процессе"
        else:
            self.status = "Не начата"
    
    def get_progress_bar(self, width=20):
        filled = int(self.progress / 100 * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}] {self.progress}%"
    
    def calculate_required_progress(self):
        if not self.due_date or self.progress == 100:
            return None, None, None
            
        today = datetime.now().date()
        due_date = datetime.strptime(self.due_date, "%Y-%m-%d").date()
        total_days = (due_date - datetime.strptime(self.created_date, "%Y-%m-%d").date()).days
        days_left = (due_date - today).days
        
        if total_days <= 0 or days_left <= 0:
            return 100, 0, "danger"
        
        required_daily = (100 - self.progress) / days_left
        actual_daily = self.progress / (total_days - days_left) if (total_days - days_left) > 0 else 0
        
        status = "success" if self.progress >= (100 * (1 - days_left/total_days)) else "warning"
        if required_daily > 10 or days_left < 3:
            status = "danger"
        
        return required_daily, days_left, status
    
    def __repr__(self):
        progress_bar = self.get_progress_bar()
        return f"Задача: {self.title} | Срок: {self.due_date} | Статус: {self.status}\nПрогресс: {progress_bar}"

class TaskManager:
    def __init__(self, filename="tasks.csv"):
        self.filename = filename
        self.tasks = []
        self.notifier = NotificationManager()
        self.load_tasks()

    def show_notification(self, title, message, duration=5):
        try:
            self.notifier.show(title, message)
        except Exception as e:
            print(f"Не удалось показать уведомление: {str(e)}")

    def update_progress(self, title, new_progress):
        for task in self.tasks:
            if task.title.lower() == title.lower():
                prev_status = task.status
                task.update_progress(new_progress)
                self.save_tasks()
                
                if task.status == "Завершена" and prev_status != "Завершена":
                    congrats_msg = f"🎉 ПОЗДРАВЛЯЕМ! Задача '{title}' завершена!"
                    print(f"\n{congrats_msg}\n")
                    self.notifier.show("ЗАДАЧА ЗАВЕРШЕНА", congrats_msg, 3)
                    return True
                
                required_daily, days_left, status = task.calculate_required_progress()
                
                if status == "success":
                    print(f"Отлично! Задача '{title}' идет по плану 👍")
                elif status == "warning":
                    print(f"Внимание! По задаче '{title}' нужно ускориться ⚠️")
                    print(f"Требуется прогресс: {required_daily:.1f}% в день")
                elif status == "danger":
                    print(f"Тревога! Задача '{title}' под угрозой срыва срока 🔥")
                    print(f"Ежедневно нужно делать: {required_daily:.1f}%")
                
                return True
        print(f"Ошибка: Задача '{title}' не найдена!")
        return False
    
    def check_progress_alerts(self, show_toast=True):
        alerts = []
        for task in self.get_pending_tasks():
            if task.due_date:
                required_daily, days_left, status = task.calculate_required_progress()
                
                if status == "danger" and days_left > 0:
                    alert_msg = f"🚨 КРИТИЧЕСКИЙ УРОВЕНЬ: '{task.title}'! Осталось {days_left} дней, требуется {required_daily:.1f}% в день"
                    alerts.append(alert_msg)
                    if show_toast:
                        self.show_notification("СРОЧНОЕ УВЕДОМЛЕНИЕ", alert_msg)
                
                elif status == "danger" and days_left <= 0:
                    alert_msg = f"🔥 ПРОСРОЧЕНО: '{task.title}'! Задача должна была быть завершена {-days_left} дней назад"
                    alerts.append(alert_msg)
                    if show_toast:
                        self.show_notification("ПРОСРОЧЕНА ЗАДАЧА", alert_msg)
                
                elif status == "warning":
                    alert_msg = f"⚠️ ВНИМАНИЕ: '{task.title}' - отставание от графика! Осталось {days_left} дней, требуется {required_daily:.1f}% в день"
                    alerts.append(alert_msg)
                    if show_toast:
                        self.show_notification("ВНИМАНИЕ: Отставание", alert_msg)
                
                elif status == "success":
                    alert_msg = f"✅ ХОРОШАЯ РАБОТА: '{task.title}' идет по плану! Осталось {days_left} дней, текущий прогресс: {task.progress}%"
                    alerts.append(alert_msg)
        if alerts:
            print("\n" + "="*60)
            print("СИСТЕМНЫЕ ОПОВЕЩЕНИЯ О ПРОГРЕССЕ:")
            for alert in alerts:
                print(f"- {alert}")
            print("="*60 + "\n")
        return alerts
    
    def load_tasks(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    task = Task(row['title'], row['due_date'], row['status'], int(row.get('progress', 0)))
                    task.created_date = row.get('created_date', datetime.now().strftime("%Y-%m-%d"))
                    self.tasks.append(task)
    
    def save_tasks(self):
        with open(self.filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['title', 'due_date', 'status', 'progress', 'created_date']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for task in self.tasks:
                writer.writerow({
                    'title': task.title,
                    'due_date': task.due_date,
                    'status': task.status,
                    'progress': task.progress,
                    'created_date': task.created_date
                })

    def add_task(self, title, due_date=None):
        if any(task.title.lower() == title.lower() for task in self.tasks):
            print(f"Ошибка: Задача '{title}' уже существует!")
            return False
            
        new_task = Task(title, due_date)
        self.tasks.append(new_task)
        self.save_tasks()
        print(f"Задача '{title}' успешно добавлена!")
        return True
    
    def start_task(self, title):
        for task in self.tasks:
            if task.title.lower() == title.lower():
                if task.status == "Завершена":
                    print(f"Ошибка: Задача '{title}' уже завершена!")
                    return False
                task.status = "В процессе"
                self.save_tasks()
                print(f"Задача '{title}' начата!")
                return True
        print(f"Ошибка: Задача '{title}' не найдена!")
        return False

    def complete_task(self, title):
        for task in self.tasks:
            if task.title.lower() == title.lower():
                task.status = "Завершена"
                self.save_tasks()
                print(f"Задача '{title}' отмечена как завершенная!")
                return True
        if task.status == "Завершена":
            print(f"Задача '{title}' уже завершена!")
            return False
        print(f"Ошибка: Задача '{title}' не найдена!")
        return False

    def get_pending_tasks(self):
        return [task for task in self.tasks if task.status != "Завершена"]
        
    def calculate_productivity(self):
        if not self.tasks:
            return 0, 0, 0
            
        completed = sum(1 for task in self.tasks if task.status == "Завершена")
        in_progress = sum(1 for task in self.tasks if task.status == "В процессе")
        pending = len(self.tasks) - completed - in_progress
        
        return completed, in_progress, pending

    def show_productivity_chart(self):
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Ошибка: Для построения диаграмм установите matplotlib!")
            print("Выполните: pip install matplotlib")
            return
        try:
            from win10toast import ToastNotifier
            TOAST_ENABLED = True
        except ImportError:
            TOAST_ENABLED = False
            print("Библиотека win10toast не установлена. Системные уведомления недоступны.")
        except:
            TOAST_ENABLED = False
            print("Системные уведомления недоступны для вашей ОС")

        completed, in_progress, pending = self.calculate_productivity()
        
        if completed == 0 and in_progress == 0 and pending == 0:
            print("Нет данных для визуализации!")
            return
            
        labels = ['Завершено', 'В процессе', 'Ожидает']
        values = [completed, in_progress, pending]
        colors = ['#2ecc71', '#3498db', '#e74c3c']
        
        plt.figure(figsize=(10, 6))
        plt.bar(labels, values, color=colors)
        plt.title('Продуктивность выполнения задач')
        plt.ylabel('Количество задач')
        
        for i, v in enumerate(values):
            plt.text(i, v + 0.2, str(v), ha='center')
            
        plt.tight_layout()
        plt.savefig('productivity_chart.png')
        print("Диаграмма сохранена как 'productivity_chart.png'")

    def check_deadlines(self):
        today = datetime.now().date()
        overdue_tasks = []
        
        for task in self.get_pending_tasks():
            if task.due_date:
                due_date = datetime.strptime(task.due_date, "%Y-%m-%d").date()
                if due_date < today:
                    overdue_tasks.append(task)
        
        return overdue_tasks

    def upcoming_deadlines(self, days=7):
        today = datetime.now().date()
        upcoming = []

        for task in self.get_pending_tasks():
            if task.due_date:
                due_date = datetime.strptime(task.due_date, "%Y-%m-%d").date()
                delta = (due_date - today).days
                if 0 <= delta <= days:
                    upcoming.append((task, delta))
        
        upcoming.sort(key=lambda x: x[1])
        return upcoming
    
class TaskManagerCLI:
    def __init__(self):
        self.manager = TaskManager()
        self.commands = {
            "add": self.add_task,
            "start": self.start_task,
            "progress": self.update_progress,
            "complete": self.complete_task,
            "list": self.list_tasks,
            "pending": self.list_pending,
            "stats": self.show_stats,
            "deadlines": self.check_deadlines,
            "upcoming": self.show_upcoming,
            "alerts": self.check_alerts,
            #"debug": self.debug_mode,
            "help": self.show_help,
            "exit": self.exit_app
        }
    
    def run(self):
        print("Добро пожаловать в TaskManager!")
        self.manager.check_progress_alerts()
        self.show_help()
        
        while True:
            try:
                command = input("\nВведите команду: ").strip().lower()
                if command in self.commands:
                    self.commands[command]()
                else:
                    print("Неизвестная команда. Введите 'help' для списка команд.")
            except KeyboardInterrupt:
                print("\nПрервано пользователем. Для выхода введите 'exit'")

    def add_task(self):
        title = input("Название задачи: ")
        due_date = input("Срок выполнения (ГГГГ-ММ-ДД, опционально): ").strip()
        self.manager.add_task(title, due_date if due_date else None)

    def start_task(self):
        title = input("Название задачи для начала выполнения: ")
        self.manager.start_task(title)

    def update_progress(self):
        title = input("Название задачи: ")
        try:
            progress = int(input("Текущий прогресс (0-100%): "))
            self.manager.update_progress(title, progress)
        except ValueError:
            print("Ошибка: Введите число от 0 до 100")

    def complete_task(self):
        title = input("Название завершенной задачи: ")
        self.manager.complete_task(title)
    
    def list_tasks(self):
        print("\nВсе задачи:")
        for i, task in enumerate(self.manager.tasks, 1):
            print(f"{i}. {task}")
    
    def list_pending(self):
        pending = self.manager.get_pending_tasks()
        print("\nНезавершенные задачи:")
        for i, task in enumerate(pending, 1):
            print(f"{i}. {task}")
    
    def show_stats(self):
        self.manager.show_productivity_chart()
        print("Диаграмма продуктивности сохранена в файл 'productivity_chart.png'")
    
    def check_deadlines(self):
        overdue = self.manager.check_deadlines()
        if overdue:
            print("\nПросроченные задачи:")
            for i, task in enumerate(overdue, 1):
                print(f"{i}. {task.title} (срок: {task.due_date})")
        else:
            print("Просроченных задач нет!")
    
    def show_upcoming(self):
        upcoming = self.manager.upcoming_deadlines()
        if upcoming:
            print("\nБлижайшие дедлайны:")
            for task, days in upcoming:
                print(f"- {task.title}: через {days} дней ({task.due_date})")
        else:
            print("Ближайших дедлайнов нет!")

    def check_alerts(self):
        alerts = self.manager.check_progress_alerts(show_toast=True)
        if not alerts:
            print("Все задачи идут по плану! 👍")
            self.manager.toast_manager.show_notification("Всё по плану", "Все задачи выполняются в срок!")
    """def debug_mode(self):
        self.manager.tasks = []
        
        today = datetime.now().date()
        
        overdue_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
        task1 = Task("Просроченный проект", overdue_date, "В процессе", 30)
        task1.created_date = (today - timedelta(days=20)).strftime("%Y-%m-%d")
        self.manager.tasks.append(task1)
        
        due_soon = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        task2 = Task("Срочный проект", due_soon, "В процессе", 20)
        task2.created_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")
        self.manager.tasks.append(task2)
        
        future_date = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        task3 = Task("Проект с опережением", future_date, "В процессе", 60)
        task3.created_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
        self.manager.tasks.append(task3)
        
        task4 = Task("Завершенный проект", status="Завершена", progress=100)
        self.manager.tasks.append(task4)
        
        task5 = Task("Проект без дедлайна")
        self.manager.tasks.append(task5)
        
        self.manager.save_tasks()
        print("Созданы тестовые задачи для отладки:")
        print("1. Просроченный проект")
        print("2. Срочный проект (критическое отставание)")
        print("3. Проект с опережением графика")
        print("4. Завершенный проект")
        print("5. Проект без дедлайна")
        
        self.check_alerts()
        
        self.list_tasks()"""
    def show_help(self):
        print("\nДоступные команды:")
        print("add      - Добавить новую задачу")
        print("start    - Начать выполнение задачи")
        print("progress - Обновить прогресс выполнения")
        print("complete - Отметить задачу как выполненную")
        print("list     - Показать все задачи")
        print("pending  - Показать незавершенные задачи")
        print("stats    - Показать статистику продуктивности")
        print("deadlines- Проверить просроченные задачи")
        print("upcoming - Показать ближайшие дедлайны")
        print("alerts   - Проверить системные оповещения")
        print("help     - Показать эту справку")
        print("exit     - Выйти из программы")
    
    def exit_app(self):
        print("Сохранение данных...")
        self.manager.save_tasks()
        print("До свидания!")
        exit()

if __name__ == "__main__":
    cli = TaskManagerCLI()
    cli.run()