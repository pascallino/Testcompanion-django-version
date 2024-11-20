from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import json
from django.http import JsonResponse


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
    


    
