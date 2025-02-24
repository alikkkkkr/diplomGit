from django.urls import path, re_path, include
import doc.views as v

urlpatterns = [
    path('', v.index, name='indexPage'),

    # Авторизация и регистрация
    path('auth/', v.auth, name='authPage'),
    path('registration/', v.register, name='regPage'),
    path('logout/', v.logout_view, name='logoutPage'),
    path('account/', v.useraccount, name='useraccountPage'),
    path('register/organization/', v.register_organization, name='register_organization'),
    path('approve/organization/<int:organization_id>/', v.approve_organization, name='approve_organization'),
    path("organization/login/", v.organization_login, name="organization_login"),
    path("organization/logout/", v.organization_logout, name="organization_logout"),

    # Парсинг данных и практиканты
    path('upload/', v.upload_interns, name='upload_interns'),
    path('interns/', v.interns_list, name='interns_list'),
    path('update_intern/<int:intern_id>/', v.update_intern, name='update_intern'),
    path('add_intern/', v.add_intern, name='add_intern'),
    path('intern_detail/<int:intern_id>/', v.intern_detail, name='intern_detail'),
    path('request_resume_access/<int:intern_id>/', v.request_resume_access, name='request_resume_access'),

    # Органиции
    path('organization_list/', v.organizations_list, name='organizations_list'),

    # Преподаватель


    # Администратор
    path('adm/', v.admin_panel, name='admin_panel'),
    path('adm/add/<str:model_name>/', v.admin_add, name='admin_add'),
    path('adm/edit/<str:model_name>/<int:pk>/', v.admin_edit, name='admin_edit'),
    path('adm/delete/<str:model_name>/<int:pk>/', v.admin_delete, name='admin_delete'),

    # Студенты
    path('student_index/', v.student_index, name='student_index'),
]
