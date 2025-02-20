from django.urls import path, re_path, include
import doc.views as v

urlpatterns = [
    # Главная страница
    path('', v.index, name='indexPage'),

    # Авторизация и регистрация
    path('auth/', v.auth, name='authPage'),
    path('registration/', v.register, name='regPage'),
    path('logout/', v.logout_view, name='logoutPage'),
    path('account/', v.useraccount, name='useraccountPage'),

    # Парсинг данных и практиканты
    path('upload/', v.upload_interns, name='upload_interns'),
    path('interns/', v.interns_list, name='interns_list'),
    path('update_intern/<int:intern_id>/', v.update_intern, name='update_intern'),
    path('add_intern/', v.add_intern, name='add_intern'),
    path('intern_detail/<int:intern_id>/', v.intern_detail, name='intern_detail'),
    path('request_resume_access/<int:intern_id>/', v.request_resume_access, name='request_resume_access'),
]
