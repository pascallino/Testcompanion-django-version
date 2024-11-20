from datetime import datetime, timedelta
import hashlib
from uuid import uuid4
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage
from django.http import Http404, JsonResponse
from .helperfunc import *
from apscheduler.triggers.date import DateTrigger
import json
from .models import *
#create your function here
from django.template.loader import render_to_string
from .scheduler import scheduler

def send_confirm_mail(recipient_email, admin_email, user_id, fullname):
    html_content = render_to_string('Confirmreg.html', {'user_id': user_id, 'fullname': fullname})
    recipients = [recipient_email, admin_email]
    email_message = EmailMessage(
            subject='Successful - Welcome to TestCompanion',
            body=html_content,
            from_email='luvpascal.ojukwu@yahoo.com',
            to=recipients,
        )
    email_message.content_subtype = 'html'  
    try:
        email_message.send()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def logout_user(request):
    logout(request)
    return render(request, 'Signin.html', {}) 

# Create your views here.
@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def login_view(request):
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        # user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            u = User.objects.filter(email=email).first()
            access_token = AccessToken.for_user(user)
            response = Response({'message': 'Login successful', 'access_token': str(access_token), 'user_id': u.userid}, status=status.HTTP_200_OK)
            response.set_cookie('access_token', value=str(access_token), httponly=False, secure=False, samesite='Lax')
            return  response
        else:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return render(request, 'Signin.html', {}) 
 
@login_required
def mainboard(request, user_id):
    user = User.objects.filter(userid=user_id).first()
    if user:
        com = Company.objects.filter(companyid=user.company_id).first()
        return render(request, 'Mainboard.html', {'user_id':user_id, 'company_name':com.company_name }) 
    return JsonResponse({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def get_user(request, user_id):
    user = User.objects.filter(userid=user_id).first()
    json_data = {}
    if user:
        json_data['firstName'] = user.first_name
        json_data['lastName'] =  user.last_name
        json_data['email'] = user.email
        json_data['status'] = 'success'
        json_data['message'] = 'success'
        json_data['role'] = user.role
        return  JsonResponse(json_data, status=200)
    else:
         json_data['eror'] = 'success'
         json_data['message'] = 'An error Occured, couldnt retrieve user data'
         return  JsonResponse(json_data, status=500)



@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def saveuser(request, user_id):
    try:
        data = json.loads(request.body)
        fn = data.get('firstName', '')
        ln = data.get('lastName', '')
        pwd = data.get('password', '')
        email = data.get('email', '')
        mod = data.get('mod', '')
        role = data.get('role', '')
        moduserid = data.get('moduserid', '')

        user = User.objects.filter(userid=user_id).first()
        # Perform necessary operations with the test_name and user_id
        if user and mod != True:
            e = User.objects.filter(email=email).first()
            if e:
                response_data = {
                'status': 'error',
                'message': 'email already exist'
            }
                return JsonResponse(response_data, status=200)
            company = get_object_or_404(Company, companyid=user.company_id)
            u = User(
            company_id=company.companyid,  # Assign the related object
            userid=str(uuid4()),
            email=email,
            first_name=fn,
            last_name=ln,
            role=role,
            password=pwd,
        )

            # Save the user instance to the database
            u.set_password(pwd)
            u.save()
            response_data = {
                'status': 'success',
                'message': 'User saved successfully'
            }
            try:
                # run_time = datetime.now() + timedelta(seconds=10) 
                # scheduler.add_job(id=f'send_newuser_mail{datetime.now()}', func=send_newuser_mail, args=[pwd, fn, email, 'luvpascal.ojukwu@yahoo.com', company.company_name],  trigger=DateTrigger(run_date=run_time), replace_existing=True)
                run_time = datetime.now() + timedelta(seconds=10) 
                #send_newuser_mail(pwd, fn, email, 'luvpascal.ojukwu@yahoo.com', company.company_name)
                scheduler.add_job(id=f'send_newuser_mail{pwd}', func=send_newuser_mail, args=(pwd, fn, email, 'luvpascal.ojukwu@yahoo.com', company.company_name), trigger='date', run_date=run_time)

            except Exception as e:
                return JsonResponse({'message': str(e)}, status=500)

            return JsonResponse(response_data, status=200)
        else:
            u = User.objects.filter(userid=moduserid).first()
            if u:
                u.first_name = fn
                u.last_name = ln
                u.email = email
                u.role = role
                u.save()
            
        # On success, you can send a response to refresh the current page
            response_data = {
                'status': 'success',
                'message': 'User saved successfully'
            }

            return JsonResponse(response_data, status=200)

    except Exception as e:
        # Handle any exceptions or errors
        error_data = {
            'status': 'error',
            'error': str(e)
        }

        return JsonResponse(error_data, status=500)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def deleteuser(request, user_id):
    data = json.loads(request.body)
    user = User.objects.filter(userid=user_id).first()
    if not user:
         return JsonResponse({'message': 'The user doesn''t exist', 'status': 'error'}, status=401)  
    # tests = Test.query.filter_by(userid=user_id).all()
    # base_url = os.path.dirname(os.path.abspath(__name__))
    # for test in tests:
    #     test_id = test.test_id
    #     if test:
    #         Q = Question.query.filter_by(test_id=test_id).all()
    #         if Q:
    #             for q in Q:
    #                 try:
    #                     imagstagjpeg = f"image_{q.question_id}_{q.test_id}.jpeg"
    #                     imagstagjpg = f"image_{q.question_id}_{q.test_id}.jpg"
    #                     imagstagpng = f"image_{q.question_id}_{q.test_id}.png"
    #                     img_path1 = os.path.join(base_url, 'static/images', imagstagjpeg)
    #                     img_path2 = os.path.join(base_url, 'static/images', imagstagjpg)
    #                     img_path3 = os.path.join(base_url, 'static/images', imagstagpng)
    #                     img_paths = [os.path.join(base_url, 'static', 'images', filename) for filename in (imagstagjpeg, imagstagjpg, imagstagpng)]

    #                     imageurl = None
    #                     for path in img_paths:
    #                         if os.path.exists(path):
    #                             os.remove(path)
    
    #                 except:
    #                     pass
    #             for q in Q:
    #                 uq = Userquestion.query.filter_by(question_id=q.question_id).all()
    #                 if uq:
    #                     for uu in uq:
    #                         db.session.delete(uu)
    #                     db.session.commit()  
    #                 for o in q.options:
    #                     db.session.delete(o)
    #                 db.session.delete(q)
    #                 db.session.commit()

    #         teststat = Teststat.query.filter_by(test_id=test_id).all()
    #         if teststat:
    #             for t in teststat:
    #                 for app in t.applicanttests:
    #                     db.session.delete(app)
    #                 db.session.delete(t)
    #                 db.session.commit()
    #         db.session.delete(test)
    #         db.session.commit()
            # t = Test.query.filter_by(userid=user_id).all()
    if user == request.user:
        user.delete()
        return redirect(login_view) 
    user.delete()
    return JsonResponse({'message': 'All records deleted', 'status': 'success'}, status=200)



@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def userboard(request, user_id):
    count = 1
    u = User.objects.filter(userid=user_id).first()
    if not u:
        return JsonResponse({'error': 'Unauthorized User'}, status=401)
    if u.role == 'user':
        return JsonResponse({'error': 'Unauthorized User'}, status=401)
    q_param = request.data.get('q')
    if q_param == 'name' and request.data.get('name') != '':
        q = request.data.get('name')
        # user_queryset = User.objects.filter(
        # ~Q(email=u.email) &
        # (Q(first_name__icontains=q) | Q(last_name__icontains=q))
        user_queryset = User.objects.filter(
        (Q(first_name__icontains=q) | Q(last_name__icontains=q))
    ).order_by('-created_at')
    else:
        # If 'q_param' is not 'name' or 'name' is empty, filter by email exclusion and order by created
        user_queryset =  User.objects.all().order_by('-created_at')

    # Get the page number from the GET request, default to 1 if not specified
    page_number = request.GET.get('page', 1)

    # Ensure the page number is a valid positive integer
    if int(page_number) <= 1:
        page_number = 1  # Fallback to the first page if the page number is invalid

    paginator = Paginator(user_queryset, 3)  # 3 items per page

    try:
        pages = paginator.page(page_number)
    except EmptyPage:
        # If the requested page number is out of range, show the last page
        pages = paginator.page(paginator.num_pages)  # Get last page in case of out-of-range page

    return render(request, 'Userdashboard.html', {
        'user': user_queryset,
        'pages': pages,
          'i': 0,
        'user_id': user_id
    })
    
def test(request):
     return render(request, 'test.html', {}) 

def index(request):
    return render(request, 'index.html', {})

def about(request):
    return render(request, 'About.html', {})

def features(request):
    return render(request, 'Features.html', {})

def contact(request):
    return render(request, 'Contact.html', {})

def signup(request):
    return render(request, 'Signup.html', {})

# def login_user(request):
#     pass



@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def send_contact_form(request):
    if request.method == 'POST':
        json_data = json.loads(request.body)
        name = json_data.get('name')
        email = json_data.get('email')
        message = json_data.get('message')
        
        body = f"{message} \n\nEmail: {email}\n\nRegards,\n{name}"
        
        email_message = EmailMessage(
            subject='Customer Mail',
            body=body,
            from_email='luvpascal.ojukwu@yahoo.com',
            to=[email],
        )
        try:
            email_message.send()
            response_data = {
                'status': 'success',
                'message': 'Thank you for reaching out to us, we have received your message, we will get in touch with you soon'
            }
            return JsonResponse(response_data, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def resend_confirm_mail(request, user_id):
    u =  json.loads(request.body)
    userid = u['user_id']
    if userid  == '' or userid is None:
        return JsonResponse({'error', 'Unauthorized user'},  status=401)
    user = User.objects.filter(userid=userid).first()
    if user:
        send_confirm_mail(user.email, 'luvpascal.ojukwu@yahoo.com', user.userid, user.last_name + ' ' + user.first_name)
        return JsonResponse({'success': 'success', 'message': 'Confirmation mail sent'}, status=200)



@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def testcompanion_confirm(request, user_id):
    user = User.objects.filter(userid=user_id).first()
    confirm = request.GET.get('confirm')
    if user:
        try:
            com = Company.objects.filter_(companyid=user.company_id).first()
            if com.confirm == True:
                pass
                #return jsonify({'error': 'link has expired'})
            if confirm == 'True':
                com.confirm = True
            com.save()
            return render(request, 'confirmation.html', {})
        except:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'link has expired'}, status=status.HTTP_401_UNAUTHORIZED)




@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def signup_post(request):
    #try:
    signup_data = json.loads(request.body)
    company_name = signup_data["company_name"]
    company_website = signup_data["company_website"]
    company_email = signup_data["company_email"]
    company_address = signup_data["company_address"]
    first_name = signup_data["first_name"]
    last_name = signup_data["last_name"]
    email = signup_data["email"]
    password = signup_data["password"]
    user = User.objects.filter(email=email).first()
    if user:
        return JsonResponse({'message': 'Record already exists.'}, status=200)
    company = Company(company_name=company_name,companyid=str(uuid4()), company_email=company_email,
                        company_website=company_website,
                        company_address=company_address)
    company.save()
    user = User(company=company,
                userid=str(uuid4()),
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='admin')
    #user.company_id = company.companyid
    user.set_password(password)
    user.save()
    send_confirm_mail(email, 'luvpascal.ojukwu@yahoo.com', user.userid, user.last_name + ' ' + user.first_name)
    return JsonResponse({'user_id': user.userid , 'message': 'Thank you for signing up, please check your email to complete your registration'}, status=200)


def Registrationsuccess(request, user_id):
    return render(request, 'Registrationsuccess.html', {'user_id':user_id})

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def get_id(request, email, pwd):
    #print(password_)
    user = User.objects.filter(email=email).first()
    if not user or not user.check_password(pwd):
        return JsonResponse({"message": "Invalid username or password"}, status=401)
    return JsonResponse({'user_id': user.userid}, status=200)