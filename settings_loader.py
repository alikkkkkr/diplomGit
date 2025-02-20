import os
import sys
import django

# Добавляем путь к проекту в PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Укажите правильное имя вашего проекта
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DiplomProject.settings')

# Инициализация Django
django.setup()