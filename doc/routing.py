from django.urls import path, re_path, include
import doc.views as v

urlpatterns = [
    path('', v.interns_list, name='indexPage'),

    # Авторизация и регистрация
    path('auth/', v.auth, name='authPage'),
    path('registration/', v.register, name='regPage'),
    path('logout/', v.logout_view, name='logoutPage'),
    path('account/', v.account, name='useraccountPage'),
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
    path('organization/<int:organization_id>/', v.organization_detail, name='organization_detail'),
    path('organizer/', v.organizer_index, name='organizer_index'),
    path('organization_list/', v.organizations_list, name='organizations_list'),
    path('organization_index/', v.organizer_index, name='organizations_index'),
    path('send_interview_invitation/', v.send_interview_invitation, name='send_interview_invitation'),
    path('organization/<int:organization_id>/', v.organization_detail, name='organization_detail'),
    path('organization/<int:organization_id>/update/', v.update_organization, name='update_organization'),
    path('supervisor/<int:supervisor_id>/update/', v.update_supervisor, name='update_supervisor'),
    path('organization/<int:organization_id>/edit/', v.edit_organization, name='edit_organization'),

    # Руководитель практики
    path('documents_page/', v.documents_page, name='documents_page'),
    path('upload_document_ajax/', v.upload_document_ajax, name='upload_document_ajax'),
    path('delete_document_ajax/<int:document_id>/', v.delete_document_ajax, name='delete_document_ajax'),
    path('get_groups/', v.get_groups, name='get_groups'),
    path('prakties/', v.prakties, name='prakties'),  # Основная страница
    path('download_filled_document_supervisor/<int:document_id>/<int:intern_id>/', v.download_filled_document_supervisor, name='download_filled_document_supervisor'),

    path('add_practice/', v.add_practice, name='add_practice'),
    path('edit_practice/<int:practice_id>/', v.edit_practice, name='edit_practice'),
    path('delete_practice/<int:practice_id>/', v.delete_practice, name='delete_practice'),

    path('add_schedule/', v.add_schedule, name='add_schedule'),
    path('edit_schedule/<int:schedule_id>/', v.edit_schedule, name='edit_schedule'),
    path('delete_schedule/<int:schedule_id>/', v.delete_schedule, name='delete_schedule'),

    path('add_group/', v.add_group, name='add_group'),
    path('edit_group/<int:group_id>/', v.edit_group, name='edit_group'),
    path('delete_group/<int:group_id>/', v.delete_group, name='delete_group'),

    # Администратор
    path('adm/', v.admin_panel, name='admin_panel'),
    path('adm/add/<str:model_name>/', v.admin_add, name='admin_add'),
    path('adm/edit/<str:model_name>/<int:pk>/', v.admin_edit, name='admin_edit'),
    path('adm/delete/<str:model_name>/<int:pk>/', v.admin_delete, name='admin_delete'),

    # Студенты
    path('student_index/', v.student_index, name='student_index'),
    path('change_password/', v.change_password, name='change_password'),
    path('send_password/<int:intern_id>/', v.send_password, name='send_password'),
    path('send-passwords-to-all-students/', v.send_passwords_to_all_students, name='send_passwords_to_all_students'),
    # path('fill_document_data/<int:document_id>/', v.fill_document_data, name='fill_document_data'),
    path('documents/<int:document_id>/download/', v.download_filled_document, name='download_filled_document'),
    path('update-skills/', v.update_intern_skills, name='update_intern_skills'),
    path('upload-resume/', v.upload_intern_resume, name='upload_intern_resume'),
    path('change-email/', v.change_student_email, name='change_student_email'),
]
