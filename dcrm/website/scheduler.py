
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django.conf import settings
from .helperfunc import *

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")


# def send_newuser_mail_job(pwd, fn, recipient_email, email, companyname):
#     scheduler.add_job(id=f'send_newuser_mail{ datetime.now()}', func=send_newuser_mail, args=(pwd, fn, email, 'setorf@yahoo.com', com.company_name), trigger='date', run_date=run_time)


def start():
    if not scheduler.running:
        scheduler.start()