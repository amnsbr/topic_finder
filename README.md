
## How to use
1. Create a virtualenv and download the requirements

> virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

2. Change the SECRET_KEY, DATA_DIR, REPO_DIR and DATABASES in the myproject/myproject/settings.py
3. Initialize Django
> cd myproject
python manage.py createsuperuser
\# enter the username and password of the admin
python manage.py migrate

4. Install redis according to https://redis.io/topics/quickstart
5. Daemonize Celery using supervisor according to the last step of https://simpleisbetterthancomplex.com/tutorial/2017/08/20/how-to-use-celery-with-django.html
6. Run Django app using:
> python manage.py runserver 0.0.0.0:8000
