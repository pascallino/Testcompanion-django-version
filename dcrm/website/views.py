import hashlib
from uuid import uuid4
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.core.mail import EmailMessage
from django.http import JsonResponse
from .helperfunc import *
import json
from .models import *
#create your function here
from django.template.loader import render_to_string


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
        return JsonResponse({'error pascal': str(e)}, status=500)


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
            access_token = AccessToken.for_user(user)
            response = Response({'message': 'Login successful', 'access_token': str(access_token) }, status=status.HTTP_200_OK)
            response.set_cookie('access_token', value=str(access_token), httponly=False, secure=False, samesite='Lax')
            return  response
        else:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    else:
         return render(request, 'Signin.html', {})  

def mainboard(request, user_id):
         return render(request, 'Mainboard.html', {'user_id':user_id}) 
    
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
def logout_user(request):
    logout(request)
    return redirect('index')


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