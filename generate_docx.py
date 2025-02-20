from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from settings_loader import *  # Загрузка настроек Django
from doc.models import Intern, Group, Organization

def fetch_students_by_groups(selected_groups):
    """
    Получает студентов по выбранным группам и группирует их по организациям.
    """
    interns = Intern.objects.filter(group__name__in=selected_groups).select_related('group', 'organization').all()

    # Словарь для группировки студентов по организациям
    grouped_data = {}
    for intern in interns:
        org_name = intern.organization.full_name if intern.organization else "Без организации"
        if org_name not in grouped_data:
            grouped_data[org_name] = []
        grouped_data[org_name].append({
            "student": f"{intern.last_name} {intern.first_name} {intern.middle_name or ''}",
            "group": intern.group.name,
            "college_supervisor": intern.college_supervisor.full_name if intern.college_supervisor else "",
            "org_supervisor": intern.organization_supervisor.full_name if intern.organization_supervisor else ""
        })

    # Разделяем организации на обычные и связанные с техникумом
    regular_organizations = {k: v for k, v in grouped_data.items() if "техникум" not in k.lower()}
    tech_organizations = {k: v for k, v in grouped_data.items() if "техникум" in k.lower()}

    return {**regular_organizations, **tech_organizations}  # Объединяем словари


def generate_docx(data, output_path):
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

    # Добавляем основной контент
    for org_name, students in data.items():
        # Добавляем название организации
        org_title = doc.add_paragraph(org_name, style="Heading 1")

        # Добавляем таблицу для студентов
        table = doc.add_table(rows=1, cols=5)
        table.style = "Table Grid"

        # Заголовки таблицы
        headers = ["ФИО студента", "Группа", "Руководитель от техникума", "Руководитель от организации", ""]
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            cell.paragraphs[0].runs[0].font.bold = True

        # Добавляем данные студентов
        for student in students:
            row_cells = table.add_row().cells
            row_cells[0].text = student["student"]
            row_cells[1].text = student["group"]
            row_cells[2].text = student["college_supervisor"]
            row_cells[3].text = student["org_supervisor"]

        # Добавляем пустую строку между организациями
        doc.add_paragraph()

    # Сохраняем документ
    doc.save(output_path)


def create_practice_bases(groups, output_file="practice_bases.docx"):
    """
    Основная функция для создания файла .docx.
    """
    try:
        data = fetch_students_by_groups(groups)
        generate_docx(data, output_file)
        print(f"Файл успешно создан: {output_file}")
    except Exception as e:
        print(f"Ошибка при создании файла: {e}")
