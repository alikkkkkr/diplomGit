import os
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .forms import *
import pandas as pd
from django.core.exceptions import ValidationError
from .models import *
from django.http import JsonResponse, Http404, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.paginator import Paginator
from docx import Document as DocxDocument


def upload_interns(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            # Чтение файла Excel
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file, sheet_name=None)  # Читаем все листы

            for sheet_name, sheet_data in df.items():
                # Извлекаем название группы из имени листа
                group_name_full = sheet_name.strip()  # Имя листа
                group_name = group_name_full.replace("Группа ", "").strip()  # Убираем слово "Группа ", если есть

                # Определяем код специальности на основе названия группы
                specialty_code = None
                if group_name.startswith(("П50", "П")):  # Программисты
                    specialty_code = "09.02.07"
                else:
                    raise ValueError(f"Неизвестная группа: {group_name}. Не удалось определить специальность.")

                # Находим специальность по коду
                specialty = Specialty.objects.filter(code=specialty_code).first()
                if not specialty:
                    raise ValueError(f"Специальность с кодом '{specialty_code}' не найдена в базе данных.")

                # Находим или создаем группу с привязкой к специальности
                group, _ = Group.objects.get_or_create(name=group_name, defaults={'specialty': specialty})

                # Явно указываем индексы столбцов
                column_mapping = {
                    "Фамилия Имя Отчество": 1,  # Столбец V (индекс 1)
                    "Ближайшее метро от дома": 2,  # Столбец C (индекс 2)
                    "Мобильный телефон": 3,  # Столбец D (индекс 3)
                    "База практики": 4,  # Столбец E (индекс 4)
                }

                # Проверяем, что данные существуют в соответствующих столбцах
                for col_name, col_idx in column_mapping.items():
                    if col_idx >= len(sheet_data.columns):
                        raise ValueError(f"Отсутствует столбец для поля: {col_name}")

                # Начинаем обработку данных с третьей строки (индекс 2)
                data_rows = sheet_data.iloc[2:]  # Начинаем с строки V3

                # Обработка строк таблицы
                for _, row in data_rows.iterrows():
                    # ФИО практиканта
                    full_name = row.iloc[column_mapping["Фамилия Имя Отчество"]]
                    if not full_name or pd.isna(full_name):  # Проверяем на пустоту или NaN
                        continue  # Пропускаем строку, если ФИО отсутствует

                    full_name_parts = full_name.split()
                    if len(full_name_parts) < 2:
                        continue  # Пропускаем строку, если ФИО некорректно
                    surname = full_name_parts[0]
                    name = full_name_parts[1]
                    patronymic = full_name_parts[2] if len(full_name_parts) > 2 else None

                    # Метро
                    metro_station = row.iloc[column_mapping["Ближайшее метро от дома"]] if pd.notna(
                        row.iloc[column_mapping["Ближайшее метро от дома"]]
                    ) else ""

                    # Телефон
                    phone_number = row.iloc[column_mapping["Мобильный телефон"]] if pd.notna(
                        row.iloc[column_mapping["Мобильный телефон"]]
                    ) else ""

                    # База практики
                    organization_name = row.iloc[column_mapping["База практики"]] if pd.notna(
                        row.iloc[column_mapping["База практики"]]
                    ) else ""

                    # Находим организацию (если существует)
                    organization = None
                    if organization_name and isinstance(organization_name, str):
                        organization, _ = Organization.objects.get_or_create(
                            full_name=organization_name.strip(),
                            defaults={
                                "legal_address": "",
                                "actual_address": "",
                                "inn": "",
                                "kpp": "",
                                "ogrn": "",
                                "phone_number": "",
                                "email": "",
                            }
                        )

                    # Создаем практиканта
                    intern = Intern(
                        last_name=surname,
                        first_name=name,
                        middle_name=patronymic,
                        phone_number=phone_number,
                        metro_station=metro_station,
                        group=group,
                        organization=organization
                    )
                    intern.clean()  # Проверяем валидность данных
                    intern.save()

            messages.success(request, "Данные успешно загружены.")
            return redirect('interns_list')

        except Exception as e:
            messages.error(request, f"Ошибка при загрузке данных: {str(e)}")

    return render(request, 'doc/upload_interns.html')


def interns_list(request):
    # Проверка авторизации
    if not request.session.get('email'):
        return redirect('authPage')

    # Получение объекта пользователя на основе email из сессии
    try:
        user = Account.objects.get(email=request.session['email'])
    except Account.DoesNotExist:
        # Если пользователь не найден, перенаправляем на страницу авторизации
        return redirect('authPage')

    # Получение списка организаций, ожидающих подтверждения
    organizations = Organization.objects.filter(is_registration_request=True, is_approved=False)

    # Получение списка практикантов
    interns = Intern.objects.all()

    # Если пользователь - руководитель практики, фильтруем по управляемым группам
    if user.role.name == 'Руководитель практики':
        managed_groups = user.managed_groups.all()
        interns = interns.filter(group__in=managed_groups)

    # Формирование контекста
    context = {
        "organizations": organizations,
        "interns": interns,
    }

    return render(request, 'doc/interns_base.html', context)


def organizer_index(request):
    # Проверка авторизации
    if not request.session.get('email'):
        return redirect('authPage')

    # Получение списка практикантов
    interns = Intern.objects.all()

    # Формирование контекста
    context = {
        "interns": interns,
    }

    return render(request, 'doc/organizer_index.html', context)


def intern_detail(request, intern_id):
    intern = get_object_or_404(Intern, id=intern_id)
    return render(request, 'doc/intern_detail.html', {'intern': intern})


def add_intern(request):
    if request.method == 'POST':
        form = InternForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('interns_list')
    else:
        form = InternForm()
    return render(request, 'doc/add_intern.html', {'form': form})


@csrf_exempt
def update_intern(request, intern_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            field = data.get('field')
            value = data.get('value')

            # Проверяем, что поле не является id или organization
            if field in ['id', 'organization']:
                return JsonResponse({'success': False, 'error': 'Редактирование этого поля запрещено.'})

            intern = Intern.objects.get(id=intern_id)

            if field == 'last_name':
                intern.last_name = value
            elif field == 'first_name':
                intern.first_name = value
            elif field == 'middle_name':
                intern.middle_name = value
            elif field == 'phone_number':
                intern.phone_number = value
            elif field == 'email':
                intern.email = value
            elif field == 'metro_station':
                intern.metro_station = value

            intern.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def request_resume_access(request, intern_id):
    if request.method == 'POST':
        try:
            intern = Intern.objects.get(id=intern_id)
            if intern.request_resume_access():
                return JsonResponse({'success': True, 'message': 'Доступ к резюме разрешен.'})
            else:
                return JsonResponse({'success': False, 'message': 'Доступ к резюме уже был разрешен.'})
        except Intern.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Практикант не найден.'})
    return JsonResponse({'success': False, 'message': 'Недопустимый метод запроса.'})


def documents_page(request):
    if not request.session.get('email'):
        return redirect('authPage')  # Перенаправляем на страницу авторизации, если пользователь не авторизован

    documents = Document.objects.filter(uploaded_by__email=request.session.get('email'))
    practices = Practice.objects.all()  # Получаем все практики
    return render(request, 'doc/documents.html', {'documents': documents, 'practices': practices})


@csrf_exempt
def upload_document_ajax(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = Account.objects.get(email=request.session.get('email'))
            document.save()
            return JsonResponse({'success': True, 'message': 'Документ успешно загружен.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Недопустимый метод запроса.'})


def fill_document_data(request, document_id):
    if request.method == 'POST':
        user = Account.objects.get(email=request.session.get('email'))
        intern = Intern.objects.filter(email=user.email).first()

        if intern:
            document = Document.objects.get(id=document_id)
            docx_file = DocxDocument(document.file.path)

            # Заполняем данные в документе
            for paragraph in docx_file.paragraphs:
                if '{{ student_name }}' in paragraph.text:
                    paragraph.text = paragraph.text.replace('{{ student_name }}',
                                                          f"{intern.last_name} {intern.first_name} {intern.middle_name}")
                if '{{ organization_name }}' in paragraph.text:
                    paragraph.text = paragraph.text.replace('{{ organization_name }}',
                                                          intern.organization.full_name if intern.organization else '')
                if '{{ supervisor_name }}' in paragraph.text:
                    paragraph.text = paragraph.text.replace('{{ supervisor_name }}',
                                                          intern.college_supervisor.last_name if intern.college_supervisor else '')

            # Сохраняем документ в памяти
            buffer = BytesIO()
            docx_file.save(buffer)
            buffer.seek(0)  # Перемещаем указатель в начало файла

            # Отправляем файл в ответе
            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename="{document.title}_filled.docx"'
            return response
        else:
            return JsonResponse({'success': False, 'message': 'Студент не найден.'})
    return JsonResponse({'success': False, 'message': 'Недопустимый метод запроса.'})


def delete_document_ajax(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    document.delete()
    return JsonResponse({'success': True, 'message': 'Документ успешно удален.'})


def get_groups(request):
    specialty_id = request.GET.get('specialty_id')
    if specialty_id:
        groups = Group.objects.filter(specialty_id=specialty_id).values('id', 'name')
        return JsonResponse({'groups': list(groups)})
    return JsonResponse({'groups': []})


def prakties(request):
    # Получение данных для всех разделов
    practices = Practice.objects.all().distinct()
    schedules = Schedule.objects.all()
    groups = Group.objects.all()
    specialties = Specialty.objects.all()

    # Если пользователь - руководитель практики, фильтруем по управляемым группам
    user = Account.objects.get(email=request.session['email'])
    if user.role.name == 'Руководитель практики':
        managed_groups = user.managed_groups.all()
        practices = practices.filter(groups__in=managed_groups)
        groups = groups.filter(id__in=managed_groups)

    context = {
        'practices': practices,
        'schedules': schedules,
        'groups': groups,
        'specialties': specialties,
    }
    return render(request, 'doc/prakties.html', context)


def add_practice(request):
    if request.method == 'POST':
        form = PracticeForm(request.POST)
        if form.is_valid():
            practice = form.save(commit=False)  # Создаем объект, но не сохраняем в базу
            practice.save()  # Сохраняем основную модель
            form.save_m2m()  # Сохраняем связи ManyToMany
            messages.success(request, 'Практика успешно добавлена.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect('prakties')


def add_schedule(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'График успешно добавлен.')
        else:
            messages.error(request, 'Ошибка при добавлении графика.')
    return redirect('prakties')


def edit_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'График успешно обновлен.')
            return redirect('prakties')
        else:
            messages.error(request, 'Ошибка при обновлении графика.')
    else:
        form = ScheduleForm(instance=schedule)
    return render(request, 'doc/edit_schedule.html', {'form': form, 'schedule': schedule})


def delete_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'График успешно удален.')
        return redirect('prakties')
    return render(request, 'doc/confirm_delete_schedule.html', {'schedule': schedule})


def add_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Группа успешно добавлена.')
        else:
            messages.error(request, 'Ошибка при добавлении группы.')
    return redirect('prakties')


def edit_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Группа успешно обновлена.')
            return redirect('prakties')
        else:
            messages.error(request, 'Ошибка при обновлении группы.')
    else:
        form = GroupForm(instance=group)
    return render(request, 'doc/edit_group.html', {'form': form, 'group': group})


def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Группа успешно удалена.')
        return redirect('prakties')
    return render(request, 'doc/confirm_delete_group.html', {'group': group})


def edit_practice(request, practice_id):
    practice = get_object_or_404(Practice, id=practice_id)
    if request.method == 'POST':
        form = PracticeForm(request.POST, instance=practice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Практика успешно обновлена.')
            return redirect('prakties')
        else:
            messages.error(request, 'Ошибка при обновлении практики.')
    else:
        form = PracticeForm(instance=practice)
    return render(request, 'doc/edit_practice.html', {'form': form, 'practice': practice})


def delete_practice(request, practice_id):
    practice = get_object_or_404(Practice, id=practice_id)
    if request.method == 'POST':
        practice.delete()
        messages.success(request, 'Практика успешно удалена.')
        return redirect('prakties')
    return render(request, 'doc/confirm_delete_practice.html', {'practice': practice})


# Главная страница
def index(request):
    if not request.session.get('email'):
        return redirect('authPage')  # Перенаправляем на авторизацию, если пользователь не авторизован

    pending_registrations_count = Organization.objects.filter(is_registration_request=True, is_approved=False).count()
    context = {
        "pending_registrations_count": pending_registrations_count,
    }

    if request.session.get("role") == "Организация":
        organization_id = request.session.get("organization_id")
        organization = Organization.objects.get(id=organization_id)
        context["organization"] = organization

    return render(request, "doc/index.html", context)


def register_organization(request):
    if request.method == "POST":
        form = OrganizationRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Заявка на регистрацию организации успешно отправлена. Ожидайте подтверждения.")
            return redirect("authPage")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = OrganizationRegistrationForm()
    return render(request, "doc/register_organization.html", {"form": form})


def organization_login(request):
    if request.method == "POST":
        form = OrganizationLoginForm(request.POST)
        if form.is_valid():
            organization = form.cleaned_data["organization"]
            # Сохраняем данные организации в сессии
            request.session["organization_id"] = organization.id
            request.session["role"] = "Организация"
            request.session["organization_name"] = organization.full_name
            messages.success(request, f"Вы успешно авторизовались как {organization.full_name}.")
            return redirect("index")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = OrganizationLoginForm()
    return render(request, "doc/organization_login.html", {"form": form})


def organization_logout(request):
    if request.session.get("role") == "Организация":
        request.session.flush()
    return redirect("index")


def organizations_list(request):
    # Получаем только те организации, которые подали заявку на регистрацию и не подтверждены
    pending_organizations = Organization.objects.filter(is_registration_request=True, is_approved=False)
    return render(request, 'doc/organizations_list.html', {'organizations': pending_organizations})


@csrf_exempt
def approve_organization(request, organization_id):
    if request.method == 'POST':
        organization = Organization.objects.get(id=organization_id)

        if not organization.is_approved:
            organization.is_approved = True
            organization.is_registration_request = False
            organization.save()

            if organization.email:
                account = Account.objects.create(
                    email=organization.email,
                    surname=organization.full_name,
                    name="Organization",
                    role=Role.objects.get(name='Организация'),
                    password=organization.password  # Используем пароль, заданный при регистрации
                )

            return JsonResponse(
                {'success': True, 'message': f'Организация "{organization.full_name}" успешно подтверждена.'})
        else:
            return JsonResponse({'success': False, 'message': 'Организация уже подтверждена.'})
    return JsonResponse({'success': False, 'message': 'Недопустимый метод запроса.'})


def student_index(request):
    return render(request, 'doc/student_index.html')


# Вывод данных пользователя из сессии
def account(request):
    if not request.session.get('email'):
        return redirect('authPage')

    user = Account.objects.get(email=request.session.get('email'))
    intern = Intern.objects.filter(email=user.email).first()

    if intern:
        # Фильтруем документы через связанные модели: Document -> Practice -> Group
        documents = Document.objects.filter(practice__groups=intern.group)
    else:
        documents = []

    return render(request, 'doc/account.html', {'documents': documents})


@csrf_exempt
def send_password(request, intern_id):
    if request.method == 'POST':
        try:
            logger.info(f"Attempting to send password for intern_id: {intern_id}")
            intern = Intern.objects.get(id=intern_id)
            if intern.email:
                account = Account.objects.get(email=intern.email)
                account.generate_and_send_password()
                return JsonResponse({'success': True, 'message': 'Пароль успешно отправлен.'})
            else:
                return JsonResponse({'success': False, 'message': 'У студента не указан email.'})
        except Intern.DoesNotExist:
            logger.error(f"Intern with id {intern_id} does not exist.")
            return JsonResponse({'success': False, 'message': 'Студент не найден.'})
        except Account.DoesNotExist:
            logger.error(f"Account for intern_id {intern_id} does not exist.")
            return JsonResponse({'success': False, 'message': 'Аккаунт студента не найден.'})
    return JsonResponse({'success': False, 'message': 'Недопустимый метод запроса.'})


@csrf_exempt
def send_passwords_to_all_students(request):
    if request.method == 'POST':
        try:
            students = Account.objects.filter(role__name='Студент', email_sent=False)
            for student in students:
                student.generate_and_send_password()
            return JsonResponse({'success': True, 'message': 'Пароли успешно отправлены всем студентам.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Недопустимый метод запроса.'})


@csrf_exempt
def change_password(request):
    if request.method == 'POST':
        if not request.session.get('email'):
            return JsonResponse({'success': False, 'error': 'Пользователь не авторизован.'})

        user = Account.objects.get(email=request.session['email'])
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')

        if not user.check_password(old_password):
            return JsonResponse({'success': False, 'error': 'Старый пароль введен неверно.'})

        if new_password != confirm_new_password:
            return JsonResponse({'success': False, 'error': 'Новый пароль и подтверждение не совпадают.'})

        user.set_password(new_password)
        user.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Недопустимый метод запроса.'})


# Реализация выхода из сессии пользователя
def logout_view(request):
    if request.session.get('email'):
        request.session.flush()  # Очистка сессии
        messages.success(request, 'Вы успешно вышли из аккаунта.')
    else:
        messages.info(request, 'Вы уже не были в системе.')
    return redirect('authPage')


# Реализация функции регистрации пользователя и сохранение его в сессии
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user_role = Role.objects.get(
                name='Руководитель практики')
            user.role = user_role
            user.save()

            # Сохраняем данные пользователя в сессию
            request.session['email'] = user.email
            request.session['role'] = user.role.name
            request.session.modified = True

            messages.success(request, 'Вы успешно зарегистрировались!')
            return redirect('indexPage')
        else:
            messages.error(request, 'Форма содержит ошибки.')
    else:
        form = UserRegisterForm()
    return render(request, 'doc/reg.html', {'form': form})


def auth(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                # Поиск пользователя по email
                user = Account.objects.get(email=email)

                # Проверка пароля
                if user.check_password(password):
                    # Сохраняем данные пользователя в сессии
                    request.session['email'] = user.email
                    request.session['role'] = user.role.name
                    request.session['user_surname'] = user.surname
                    request.session['user_name'] = user.name
                    request.session['user_patronymic'] = user.patronymic
                    request.session.modified = True

                    # Перенаправление в зависимости от роли
                    if user.role.name == "Руководитель практики":
                        return redirect('indexPage')  # Перенаправление на главную страницу
                    elif user.role.name == "Организация":
                        return redirect('organizations_index')
                    elif user.role.name == "Администратор":
                        return redirect('admin_panel')  # Перенаправление на панель администратора
                    elif user.role.name == "Студент":
                        return redirect('useraccountPage')  # Перенаправление на страницу студента
                    else:
                        messages.error(request, 'Неизвестная роль пользователя.')
                        return redirect('auth')  # Возвращаем обратно на страницу авторизации
                else:
                    messages.error(request, 'Неверный email или пароль.')
            except Account.DoesNotExist:
                messages.error(request, 'Пользователь с таким email не найден.')
        else:
            messages.error(request, 'Некорректные данные в форме.')
    else:
        form = LoginForm()

    return render(request, 'doc/auth.html', {'form': form})


def admin_panel(request):
    # Получаем данные для всех моделей с пагинацией
    accounts = Account.objects.all().order_by('surname')  # Сортировка по фамилии
    interns = Intern.objects.all().order_by('last_name')
    groups = Group.objects.all()
    organizations = Organization.objects.all()
    supervisors = CollegeSupervisor.objects.all()
    specialties = Specialty.objects.all()
    org_supervisors = OrganizationSupervisor.objects.all()
    roles = Role.objects.all()
    tags = Tag.objects.all()
    schedules = Schedule.objects.all()
    practices = Practice.objects.all()

    # Фильтрация аккаунтов по роли
    selected_role = request.GET.get('role')
    if selected_role:
        accounts = accounts.filter(role_id=selected_role)

    # Фильтрация студентов по группе
    selected_group = request.GET.get('group')
    if selected_group:
        interns = interns.filter(group_id=selected_group)

    # Пагинация для всех моделей
    paginator_accounts = Paginator(accounts, 30)
    paginator_interns = Paginator(interns, 30)
    paginator_groups = Paginator(groups, 20)
    paginator_organizations = Paginator(organizations, 20)
    paginator_supervisors = Paginator(supervisors, 20)
    paginator_specialties = Paginator(specialties, 20)
    paginator_org_supervisors = Paginator(org_supervisors, 20)
    paginator_roles = Paginator(roles, 10)
    paginator_tags = Paginator(tags, 10)
    paginator_schedules = Paginator(schedules, 20)
    paginator_practices = Paginator(practices, 20)

    page_number = request.GET.get('page')
    accounts_page = paginator_accounts.get_page(page_number)
    interns_page = paginator_interns.get_page(page_number)
    groups_page = paginator_groups.get_page(page_number)
    organizations_page = paginator_organizations.get_page(page_number)
    supervisors_page = paginator_supervisors.get_page(page_number)
    specialties_page = paginator_specialties.get_page(page_number)
    org_supervisors_page = paginator_org_supervisors.get_page(page_number)
    roles_page = paginator_roles.get_page(page_number)
    tags_page = paginator_tags.get_page(page_number)
    schedules_page = paginator_schedules.get_page(page_number)
    practices_page = paginator_practices.get_page(page_number)

    context = {
        'accounts': accounts_page,
        'interns': interns_page,
        'groups': groups_page,
        'organizations': organizations_page,
        'supervisors': supervisors_page,
        'specialties': specialties_page,
        'org_supervisors': org_supervisors_page,
        'roles': roles_page,
        'tags': tags_page,
        'schedules': schedules_page,
        'practices': practices_page,
        'all_groups': groups,  # Для выпадающего списка групп
        'all_roles': roles,  # Для выпадающего списка ролей
    }
    return render(request, 'doc/admin_panel.html', context)


def admin_add(request, model_name):
    try:
        # Получаем класс формы для указанной модели
        form_class = get_form_by_model_name(model_name)
    except ValueError as e:
        raise Http404(str(e))  # Возвращаем 404, если модель не найдена

    if request.method == 'POST':
        # Создаем экземпляр формы с переданными данными
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f'Запись успешно добавлена.')
            return redirect('admin_panel')
        else:
            messages.error(request, 'Ошибка при добавлении записи.')
    else:
        # Создаем пустую форму для GET-запроса
        form = form_class()

    # Подготавливаем данные о полях формы для передачи в шаблон
    form_fields = []
    for field_name, field in form.fields.items():
        field_data = {
            'field': form[field_name],  # Объект поля формы
            'related_model_name': None,  # По умолчанию нет связанной модели
        }

        # Проверяем, является ли поле связанным с другой моделью
        if hasattr(form.Meta.model, field_name) and hasattr(getattr(form.Meta.model, field_name), 'field'):
            related_model = getattr(form.Meta.model, field_name).field.related_model
            if related_model:
                field_data['related_model_name'] = related_model._meta.model_name

        form_fields.append(field_data)

    return render(request, 'doc/admin_add.html', {
        'form': form,
        'form_fields': form_fields,  # Передаем данные о полях формы
        'model_name': model_name,
    })


def admin_edit(request, model_name, pk):
    model = get_model_by_name(model_name)
    instance = get_object_or_404(model, id=pk)

    if request.method == 'POST':
        form = get_form_by_model_name(model_name)(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Запись успешно обновлена.')
            return redirect('admin_panel')
        else:
            messages.error(request, 'Ошибка при обновлении записи.')
    else:
        form = get_form_by_model_name(model_name)(instance=instance)

    return render(request, 'doc/admin_edit.html', {'form': form, 'model_name': model_name, 'pk': pk})


def admin_delete(request, model_name, pk):
    model = get_model_by_name(model_name)
    instance = get_object_or_404(model, id=pk)

    if request.method == 'POST':
        instance.delete()
        messages.success(request, f'Запись успешно удалена.')
        return redirect('admin_panel')

    return render(request, 'doc/admin_delete.html', {'model_name': model_name, 'pk': pk})


# Вспомогательные функции
def get_model_by_name(model_name):
    """
    Возвращает класс модели по её имени.

    :param model_name: Имя модели (строка).
    :return: Класс модели.
    :raises ValueError: Если модель с таким именем не найдена.
    """
    models_dict = {
        'intern': Intern,
        'group': Group,
        'organization': Organization,
        'college_supervisor': CollegeSupervisor,
        'specialty': Specialty,
        'org_supervisor': OrganizationSupervisor,
        'role': Role,
        'tag': Tag,
        'schedule': Schedule,
        'practice': Practice,
        'account': Account,  # Добавлена модель Account
        'document': Document,  # Добавлена модель Document
        'student': Student,  # Добавлена модель Student
    }
    model_class = models_dict.get(model_name)
    if model_class is None:
        raise ValueError(f"Модель с именем '{model_name}' не найдена.")
    return model_class


def get_form_by_model_name(model_name, *args, **kwargs):
    """
    Возвращает класс формы для модели по её имени.

    :param model_name: Имя модели (строка).
    :param args: Аргументы для передачи в форму.
    :param kwargs: Ключевые аргументы для передачи в форму.
    :return: Класс формы.
    :raises ValueError: Если форма для модели не найдена.
    """
    forms_dict = {
        'intern': InternForm,
        'group': GroupForm,
        'organization': OrganizationForm,
        'college_supervisor': CollegeSupervisorForm,
        'specialty': SpecialtyForm,
        'org_supervisor': OrganizationSupervisorForm,
        'role': RoleForm,
        'tag': TagForm,
        'schedule': ScheduleForm,
        'practice': PracticeForm,
        'account': AccountForm,
        'document': DocumentForm,
        'student': StudentForm,
    }
    form_class = forms_dict.get(model_name)
    if form_class is None:
        raise ValueError(f"Форма для модели '{model_name}' не найдена.")
    return form_class
