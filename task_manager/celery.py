# Створимо файл celery.py в корені проекту
# task_manager/celery.py
import os
from celery import Celery

# Встановлюємо дефолтні налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_manager.settings')

app = Celery('task_manager')

# Використовуємо конфіг Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматично знаходимо таски в додатках
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')