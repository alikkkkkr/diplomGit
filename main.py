import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ttkthemes import ThemedStyle
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from settings_loader import *  # Загрузка настроек Django
from doc.models import Intern, Group, Organization  # Импортируйте нужные модели


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
        generate_docx(selected_groups, output_path)
        messagebox.showinfo("Успех", f"Файл успешно создан: {output_path}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при создании файла: {e}")


# Функция для генерации документа
def generate_docx(selected_groups, output_path):
    """
    Создает и сохраняет файл .docx на основе шаблона.
    """
    doc = Document()

    # Добавляем заголовок
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Базы производственной практики")
    run.font.size = Pt(16)
    run.bold = True

    # Добавляем подзаголовок
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("(по профилю специальности)")
    run.font.size = Pt(14)

    # Получаем данные студентов по группам
    interns = Intern.objects.filter(group__name__in=selected_groups).select_related('group', 'organization').all()

    # Группируем студентов по организациям
    grouped_data = {}
    for intern in interns:
        org_name = intern.organization.full_name if intern.organization else "Без организации"
        if org_name not in grouped_data:
            grouped_data[org_name] = []
        grouped_data[org_name].append({
            "student": f"{intern.last_name} {intern.first_name} {intern.middle_name or ''}",
            "group": intern.group.name,
            "college_supervisor": intern.college_supervisor.last_name if intern.college_supervisor else "",
            "org_supervisor": intern.organization.phone_number if intern.organization else ""
        })

    # Разделяем организации на обычные и связанные с техникумом
    regular_organizations = {k: v for k, v in grouped_data.items() if "техникум" not in k.lower()}
    tech_organizations = {k: v for k, v in grouped_data.items() if "техникум" in k.lower()}

    # Объединяем словари
    grouped_data = {**regular_organizations, **tech_organizations}

    # Добавляем основной контент
    for org_name, students in grouped_data.items():
        # Добавляем название организации
        org_title = doc.add_paragraph(org_name)
        org_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
        org_title.runs[0].font.bold = True

        # Добавляем таблицу для студентов
        table = doc.add_table(rows=1, cols=5)
        table.style = "Table Grid"

        # Заголовки таблицы
        headers = ["№ п/п", "ФИО студента", "Группа", "Руководитель от техникума", "Руководитель от организации"]
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            cell.paragraphs[0].runs[0].font.bold = True

        # Добавляем данные студентов
        for idx, student in enumerate(students, start=1):
            row_cells = table.add_row().cells
            row_cells[0].text = str(idx)  # Номер по порядку
            row_cells[1].text = student["student"]
            row_cells[2].text = student["group"]
            row_cells[3].text = student["college_supervisor"]
            row_cells[4].text = student["org_supervisor"]

        # Добавляем пустую строку между организациями
        doc.add_paragraph()

    # Сохраняем документ
    doc.save(output_path)


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

# Кнопка для генерации файла
generate_button = ttk.Button(button_frame, text="Создать файл .docx", command=create_docx_file, style="TButton")
generate_button.pack(side=tk.LEFT, padx=5)

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

# Настройка ширины столбцов
table.column("ID", width=50, anchor=tk.CENTER)  # Уменьшаем ширину столбца ID
table.column("Фамилия", width=150, anchor=tk.W)
table.column("Имя", width=150, anchor=tk.W)
table.column("Отчество", width=150, anchor=tk.W)
table.column("Телефон", width=120, anchor=tk.CENTER)
table.column("Метро", width=120, anchor=tk.CENTER)
table.column("Группа", width=120, anchor=tk.CENTER)
table.column("Организация", width=250, anchor=tk.W)

# Заголовки таблицы
for col in columns:
    table.heading(col, text=col)


# Привязка ширины таблицы к ширине окна
def resize_table(event):
    table_frame.update_idletasks()
    table_width = table_frame.winfo_width()
    table.column("#0", width=0, stretch=tk.NO)  # Скрываем первый столбец
    for col in columns:
        table.column(col, width=int(table_width / len(columns)), stretch=tk.YES)


table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Привязка изменения размера окна к функции resize_table
root.bind("<Configure>", resize_table)

# Скроллбар
scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=table.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
table.configure(yscrollcommand=scrollbar.set)

# Загрузка данных
students_data = fetch_students()
update_table(students_data)

# Запуск приложения
root.mainloop()
