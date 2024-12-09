from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import json
from django.http import JsonResponse
from datetime import datetime
from website.models import  User, Company, Emailserver, Teststat, Applicanttest, Question, Option, Userquestion, Test


def send_confirm_mail(recipient_email, admin_email, user_id, fullname):
    html_content = render_to_string('Confirmreg.html', user_id=user_id, fullname=fullname)
    recipients = [recipient_email, admin_email]
    email_message = EmailMessage(
            subject='Successful - Welcome to TestCompanion',
            body=html_content,
            from_email='luvpascal.ojukwu@yahoo.com',
            to=[recipients],
        )
    email_message.content_subtype = 'html'  
    try:
        email_message.send()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def send_newuser_mail(pwd, fn, recipient_email, email, companyname):
    #context = {"user_id": '919632aef5f4719949c0ce99413521a', "fullname": fn, 'ul': url}
    context = {
        'pd': pwd,
        'nm': fn,
        'contactemail': email,
        'companyname': companyname,
    }
    html_content = render_to_string('Usercreated.html', context=context)

    recipients = [recipient_email, recipient_email]
    email_message = EmailMessage(
            subject='New Member Registration - TestCompanion',
            body=html_content,
            from_email='luvpascal.ojukwu@yahoo.com',
            to=recipients,
        )
    email_message.content_subtype = 'html'  
    try:
        email_message.send()
    except Exception as e:
        return JsonResponse({'error pascal': str(e)}, status=500)

def send_applicantmail(recipient_email, applicantname, testdate, duration, testName, yourCompanyName,
                       companyAddress, admin_email, admin_name, user_id, key):
    context =  {'yourCompanyName': yourCompanyName, 'companyAddress': companyAddress,
                                        'applicantname': applicantname, 'testdate': testdate, 'duration': duration, 'admin_name': admin_name,
                                        'admin_email': admin_email, 'testName': testName, 'user_id': user_id, 'key': key}
    html_content = render_to_string('email_template.html', context=context)
    recipients = [recipient_email, admin_email]
    email_message = EmailMessage(
            subject= 'Upcoming Test',
            body=html_content,
            from_email='luvpascal.ojukwu@yahoo.com',
            to=recipients,
        )
    email_message.content_subtype = 'html'  
    try:
        email_message.send()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def send_reschedule_mail(name, new_test_date, testname, recipient_email):
     context = {
         'name': name, 'new_test_date': new_test_date,
                                        'testname': testname,
                                        'recipient_email': recipient_email}
     html_content = render_to_string('Testreschedule.html', context=context)
     recipients = [recipient_email]
     email_message = EmailMessage(
                subject= 'Test Reschedule Notification',
                body=html_content,
                from_email='luvpascal.ojukwu@yahoo.com',
                to=recipients,
            )
     email_message.content_subtype = 'html'  
     try:
         email_message.send()
     except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
     
def send_canceltest_mail(name, testname, recipient_email):
    context = { 'name':name, 'testname':testname, 'recipient_email':recipient_email}
    html_content = render_to_string('Testcancel.html', context=context)
    recipients = [recipient_email]
    email_message = EmailMessage(
                subject= 'Test Cancellation Notice',
                body=html_content,
                from_email='luvpascal.ojukwu@yahoo.com',
                to=recipients,
            )
    email_message.content_subtype = 'html'  
    try:
         email_message.send()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def send_test_mail(test_day_id, user_id):
    applicant = Applicanttest.objects(user_id=user_id).first()
    teststat = Teststat.objects(test_day_id=test_day_id).first()
    test = Test.objects(test_id=teststat.test_id.test_id).first()
    user = User.objects.filter(userid=test.userid).first()
    com = Company.objects.filter(companyid=user.company_id).first()
    recipient_email = applicant.user_email
    # username = "John Doe"
    # company = "Sample Company"
    yourCompanyName = com.company_name
    companyAddress = com.company_address
    testScore = applicant.score
    testName = test.test_name
    context = {
        'yourCompanyName':yourCompanyName, 'companyAddress':companyAddress,
                                    'testName':testName, 
                                    'testScore':testScore, 
                                    'applicant':applicant.fullname}
    
    html_content = render_to_string('testsubmitted.html', context=context)
    recipients = [recipient_email, 'luvpascal.ojukwu@yahoo.com']
    email_message = EmailMessage(
                subject= testName +' GRADED'  ,
                body=html_content,
                from_email='luvpascal.ojukwu@yahoo.com',
                to=recipients,
            )
    email_message.content_subtype = 'html'  
    try:
         email_message.send()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def validate_and_format_datetime(date, time):
    try:
        # Combine date and time into a datetime object
        time = f"{time}:00"
        combined_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
        return combined_datetime
    except ValueError:
        return None


    
