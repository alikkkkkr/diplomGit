from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .forms import *
import pandas as pd
from django.core.exceptions import ValidationError
from .models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


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
    interns = Intern.objects.all()
    return render(request, 'doc/interns_base.html', {'interns': interns})


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

            intern = Intern.objects.get(id=intern_id)

            if field == 'last_name':
                intern.last_name = value
            elif field == 'first_name':
                intern.first_name = value
            elif field == 'middle_name':
                intern.middle_name = value
            elif field == 'phone_number':
                intern.phone_number = value
            elif field == 'metro_station':
                intern.metro_station = value
            elif field == 'organization':
                organization, _ = Organization.objects.get_or_create(full_name=value)
                intern.organization = organization

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


# Главная страница
def index(request):
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
            return redirect("indexPage")
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
        organization.is_approved = True
        organization.is_registration_request = False  # Снимаем флаг заявки на регистрацию
        organization.save()
        return JsonResponse(
            {'success': True, 'message': f'Организация "{organization.full_name}" успешно подтверждена.'})
    return JsonResponse({'success': False, 'message': 'Недопустимый метод запроса.'})


# Вывод данных пользователя из сессии
def useraccount(request):
    if request.session.get('email'):
        email = request.session['email']
        try:
            user = Account.objects.get(email=email)
            return render(request, 'doc/account.html', {'user': user})
        except Account.DoesNotExist:
            messages.error(request, 'Пользователь не найден.')
            return redirect('authPage')
    else:
        return redirect('authPage')


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
            user_role = Role.objects.get(name='Преподаватель')  # Предполагается, что роль "Пользователь" существует
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


# Реализация функции авторизации пользователя и сохранение его в сессии
def auth(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = Account.objects.get(email=email)
                if check_password(password, user.password):
                    # Сохраняем данные пользователя в сессию
                    request.session['email'] = user.email
                    request.session['role'] = user.role.name
                    request.session.modified = True

                    return redirect('indexPage')  # После успешной авторизации перенаправляем на главную страницу
                else:
                    messages.error(request, 'Неверный email или пароль.')
            except Account.DoesNotExist:
                messages.error(request, 'Пользователь не найден.')
    else:
        form = LoginForm()
    return render(request, 'doc/auth.html', {'form': form})


def admin_panel(request):
    # Получаем данные для всех моделей
    interns = Intern.objects.all()
    groups = Group.objects.all()
    organizations = Organization.objects.all()
    supervisors = CollegeSupervisor.objects.all()
    specialties = Specialty.objects.all()
    org_supervisors = OrganizationSupervisor.objects.all()

    context = {
        'interns': interns,
        'groups': groups,
        'organizations': organizations,
        'supervisors': supervisors,
        'specialties': specialties,
        'org_supervisors': org_supervisors,
    }
    return render(request, 'doc/admin_panel.html', context)


def admin_add(request, model_name):
    if request.method == 'POST':
        form = get_form_by_model_name(model_name, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Запись успешно добавлена.')
            return redirect('admin_panel')
        else:
            messages.error(request, 'Ошибка при добавлении записи.')
    else:
        form = get_form_by_model_name(model_name)

    return render(request, 'doc/admin_add.html', {'form': form, 'model_name': model_name})


def admin_edit(request, model_name, pk):
    model = get_model_by_name(model_name)
    instance = get_object_or_404(model, id=pk)

    if request.method == 'POST':
        form = get_form_by_model_name(model_name, request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Запись успешно обновлена.')
            return redirect('admin_panel')
        else:
            messages.error(request, 'Ошибка при обновлении записи.')
    else:
        form = get_form_by_model_name(model_name, instance=instance)

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
    models_dict = {
        'intern': Intern,
        'group': Group,
        'organization': Organization,
        'college_supervisor': CollegeSupervisor,
        'specialty': Specialty,
        'org_supervisor': OrganizationSupervisor,
    }
    return models_dict.get(model_name)


def get_form_by_model_name(model_name, *args, **kwargs):
    forms_dict = {
        'intern': InternForm,
        'group': GroupForm,
        'organization': OrganizationForm,
        'college_supervisor': CollegeSupervisorForm,
        'specialty': SpecialtyForm,
        'org_supervisor': OrganizationSupervisorForm,
    }
    form_class = forms_dict.get(model_name)
    return form_class(*args, **kwargs)
