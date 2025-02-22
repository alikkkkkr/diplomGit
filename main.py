import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ttkthemes import ThemedStyle

import generate_docx
from settings_loader import *  # Загрузка настроек Django
from doc.models import Intern, Group, Organization  # Импортируйте нужные модели


# сделать загрузку файла базы практик по группам
# группировка по группам
# мин макс врап текст таблица
# просмотр данных студента?
# парсинг данных?
# круд?


# Функция для получения списка студентов
def fetch_students():
    try:
        interns = Intern.objects.select_related('group', 'organization').all()
        data = [
            (
                intern.id,
                intern.last_name,
                intern.first_name,
                intern.middle_name or "",
                intern.phone_number or "",
                intern.metro_station or "",
                intern.group.name if intern.group else "",
                intern.organization.full_name if intern.organization else ""
            )
            for intern in interns
        ]
        return data
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при получении данных: {e}")
        return []


# Функция для фильтрации студентов по поиску
def filter_students(search_text):
    if search_text.strip() == "":
        update_table(students_data)
    else:
        filtered = [student for student in students_data if any(
            search_text.lower() in str(value).lower() for value in student[1:]
        )]
        update_table(filtered)


# Функция для фильтрации студентов по группе
def filter_by_group(group_name):
    if group_name == "Все группы":
        update_table(students_data)
    else:
        filtered = [student for student in students_data if student[6] == group_name]
        update_table(filtered)


# Обновление таблицы студентов
def update_table(data):
    for row in table.get_children():
        table.delete(row)
    for student in data:
        table.insert("", "end", values=student)


# Функция для создания файла .docx
def create_docx_file():
    selected_groups = [group_var.get()] if group_var.get() != "Все группы" else list(
        Group.objects.values_list('name', flat=True))
    if not selected_groups:
        messagebox.showwarning("Предупреждение", "Выберите хотя бы одну группу.")
        return

    # Открываем диалог для выбора пути сохранения
    output_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word Files", "*.docx")])
    if not output_path:
        return

    try:
        generate_docx.create_practice_bases(selected_groups, output_path)
        messagebox.showinfo("Успех", f"Файл успешно создан: {output_path}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при создании файла: {e}")


# Создание главного окна
root = tk.Tk()
root.title("Список студентов")
root.geometry("1200x700")
root.configure(bg="white")

# Стиль для красивого дизайна
style = ThemedStyle(root)
style.set_theme("arc")  # Используем светлую тему

# Настройка цветовой палитры
style.configure("TLabel", font=("Oswald", 14), foreground="#333", background="white")
style.configure("TButton", font=("Oswald", 12, "bold"), background="#f8f9fa", foreground="#333", padding=10,
                borderwidth=1)
style.map("TButton", background=[("active", "#e9ecef")])  # Светлый фон при наведении
style.configure("TEntry", font=("Oswald", 12), foreground="#333", background="white", padding=5)
style.configure("Treeview", font=("Oswald", 12), rowheight=30, background="white", foreground="#333",
                fieldbackground="white")
style.configure("Treeview.Heading", font=("Oswald", 14, "bold"), background="#f8f9fa",
                foreground="#333")  # Темный текст на заголовках
style.map("Treeview", background=[("selected", "#E0E0E0")])

# Верхняя панель с заголовком и кнопками
header_frame = ttk.Frame(root)
header_frame.pack(pady=20, padx=20, fill=tk.X)

title_label = ttk.Label(header_frame, text="Список студентов", font=("Oswald", 24, "bold"))
title_label.pack(side=tk.LEFT)

button_frame = ttk.Frame(header_frame)
button_frame.pack(side=tk.RIGHT)

upload_button = ttk.Button(button_frame, text="Загрузить файл Excel", style="TButton")
upload_button.pack(side=tk.LEFT, padx=5)

add_button = ttk.Button(button_frame, text="Добавить студента", style="TButton")
add_button.pack(side=tk.LEFT, padx=5)

# Поиск и фильтр
filter_frame = ttk.Frame(root)
filter_frame.pack(pady=10, padx=20, fill=tk.X)

search_label = ttk.Label(filter_frame, text="Поиск:")
search_label.pack(side=tk.LEFT, padx=5)

search_entry = ttk.Entry(filter_frame, width=40)
search_entry.pack(side=tk.LEFT, padx=5)

search_button = ttk.Button(filter_frame, text="Найти", command=lambda: filter_students(search_entry.get()))
search_button.pack(side=tk.LEFT, padx=5)

group_label = ttk.Label(filter_frame, text="Группа:")
group_label.pack(side=tk.LEFT, padx=10)

groups = ["Все группы"] + list(Group.objects.values_list('name', flat=True))
group_var = tk.StringVar(value="Все группы")
group_dropdown = ttk.Combobox(filter_frame, textvariable=group_var, values=groups, state="readonly", width=20)
group_dropdown.pack(side=tk.LEFT, padx=5)

filter_group_button = ttk.Button(filter_frame, text="Применить", command=lambda: filter_by_group(group_var.get()))
filter_group_button.pack(side=tk.LEFT, padx=5)

# Таблица студентов
table_frame = ttk.Frame(root)
table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

columns = ("ID", "Фамилия", "Имя", "Отчество", "Телефон", "Метро", "Группа", "Организация")
table = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

for col in columns:
    table.heading(col, text=col)
    table.column(col, width=150, anchor=tk.CENTER)

table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Скроллбар
scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=table.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
table.configure(yscrollcommand=scrollbar.set)

# Загрузка данных
students_data = fetch_students()
update_table(students_data)

# Запуск приложения
root.mainloop()
