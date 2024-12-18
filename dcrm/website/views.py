

import hashlib
import os
import shutil
import pytz
from uuid import uuid4
from bson import ObjectId
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
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
from website.models import  User, Company, Emailserver, Teststat, Applicanttest, Question, Option, Userquestion, Test
#create your function here
from django.template.loader import render_to_string
from .scheduler import scheduler
from dcrm.settings import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST
from django.core.files.storage import default_storage
import datetime
from django.utils.timezone import activate
from django.utils import timezone
from django.utils.timezone import make_aware, utc, is_aware, is_naive


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def set_timezone(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        timezone = data.get('timezone')
        if timezone:
            request.session['timezone'] = timezone  # Store in session
            activate(timezone)  # Activate the time zone for the request
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


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
        timezone_ = request.data.get('timezone')
        if timezone_:
            request.session['timezone'] = timezone_  # Store in session
            activate(timezone_)
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
                run_time = datetime.datetime.now() + datetime.timedelta(seconds=10) 
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

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def dashboard(request, user_id):
    # get the company id through the user id
    #use it to filter all users for the company
    timezone_ = request.session['timezone']  # Store in session
    if timezone_:
        activate(timezone_)
    count = 1
    start_date = ''
    end_date = ''
    ed = None
    sd = None
    q_param = request.data.get('q')
    if q_param == 'date' and request.data.get('start-date') != '' and request.data.get('end-date') != '':
        start_date = datetime.datetime.strptime(request.data.get('start-date'), '%Y-%m-%d')
        end_date = datetime.datetime.strptime(request.data.get('end-date'), '%Y-%m-%d')
        test_queryset = Test.objects(userid=user_id)\
             .filter(created__gte=start_date, created__lte=end_date)\
            .order_by('-created')
        sd = request.data.get('start-date')
        ed = request.data.get('end-date')
    else:
        test_queryset = Test.objects(userid=user_id).order_by('-created')
    if not test:
        return JsonResponse({'error': 'Unauthorized User'}, status=401)
    user = User.objects.filter(userid=user_id).first()
    if not user:
        return JsonResponse({'error': 'Unauthorized User'}, status=401)
    users = User.objects.all()
    page_number = request.GET.get('page', 1)
    # Ensure the page number is a valid positive integer
    if int(page_number) <= 1:
        page_number = 1  # Fallback to the first page if the page number is invalid
    paginator = Paginator(test_queryset, 3)  # 3 items per page
    try:
        pages = paginator.page(page_number)
    except EmptyPage:
        # If the requested page number is out of range, show the last page
        pages = paginator.page(paginator.num_pages) 
    return render(request, 'Dashboard.html', {
        'timezone_': timezone_,
        'test': test_queryset,
        'pages': pages,
          'i': 0,
        'user_id': user_id,
        'user':user,
        'users':users,
        'test':test,
        'sd':sd,
        'ed':ed,
        'companyname':''
    })
    return render_template('Dashboard.html', test=test, i=0, pages=pages,
                           companyname='', user=user, users=users, user_id=user_id, sd=sd, ed=ed)
@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def savetest(request, user_id):
    try:
        data = json.loads(request.body)
        test_name = data.get('testname', '')
        user = User.objects.filter(userid=user_id).first()
        timezone_ = data.get('timezone', '')
        if timezone_:
            activate(timezone_)
        # Perform necessary operations with the test_name and user_id
        if user and test_name != '':
            test = Test(test_name=test_name, created=timezone.localtime(timezone.now()))
            test.test_id = str(uuid4())
            test.userid=user.userid
            #user.tests.append(test)
            test.save()
        # On success, you can send a response to refresh the current page
            response_data = {
                'status': 'success',
                'message': 'Test saved successfully'
            }

            return JsonResponse(response_data, status=200)

    except Exception as e:
        # Handle any exceptions or errors
        error_data = {
            'status': 'error',
            'error': str(e)
        }

        return JsonResponse(error_data, status=500)
    return JsonResponse({
            'status': 'error',
            'error': 'Unauthorized user'
        }, status=401)

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def editquestion(request, test_id, user_id):
    test = Test.objects(test_id=test_id).first()
    if test:
        teststat = Teststat.objects(test_id=test, status='taken').all()
        if teststat:
            for testday in teststat:
                applicant = Applicanttest.objects(test_day_id=testday, test_status='pending').first()
                if applicant:
                    message = f"for test with duration: {testday.duration} minutes \n and  test date: {testday.test_date}"
                    return render(request, 'computescoremessage.html', {'message':message, 'user_id':user_id})
        return render(request, 'editquestion.html', {
            'test_id':test_id, 'testname':test.test_name, 'user_id':user_id})

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def get_test(request, user_id):
    tests = Test.objects.filter(userid=user_id).order_by('-created').all()
    if tests:
        test_names = [{'id': test.test_id, 'name': test.test_name, 'created': test.created.strftime('%m/%d/%Y %I:%M:%S %p')} for test in tests]
        return JsonResponse(test_names, status=200, safe=False)
    else:
        return JsonResponse({'error': 'No tests found'}, status=200)

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([])
def question_post(request):
    args = ''
    try:
     args =  request.GET.get('hash', '')
    except:
        args = ''
    if request.method == 'POST' and args == '':
        json_data = json.loads(request.body)
        data_dict = json_data
        test_id = data_dict.get('test_id', '')
        q = None
        count = 0
        for key, value in data_dict.items():
            k = str(key)
            key = k.split('-')[0]
            if key.startswith("question_text_"):
                count += 1
                id = k.split('-')[1]
                # Deleting existing question and options
                ques = Question.objects(question_id=id).first()
                opts = Option.objects(question_id=ques).all()
                for opt in opts:
                    opt.delete()
                ques = Question.objects(question_id=id).first()
                if ques:
                    Test.objects.update(pull__questions=ques)
                    ques.delete()
                num = key.split("_")[-1]  # Extract the num from the key
                option_key = f"option_text_{num}"
                correct_key = f"correct_option_{num}[]"
                if data_dict.get(correct_key, "") == '':
                    correct_key = f"correct_option_{num}"
                question_text = value.strip() 
                if question_text == '':
                    continue
                correct_option = data_dict.get(correct_key, "")
                correct_str = ''
                for c in range(len(correct_option)):
                    if c < len(correct_option) - 1:
                        correct_str += correct_option[c] + ','
                    else:
                        correct_str += correct_option[c] 
                test = Test.objects(test_id=test_id).first()
                q = Question(question_id=id, text=question_text,
                             Qnum=count, correct_answer=correct_str)
                q.test_id = test.test_id
                #db.session.add(test)
                q.save()
                test.questions.append(q)
                test.save()
                # Adding new options
                try:
                    for i in range(10):
                        option_text = data_dict.get(f"{option_key}_{i}", "")
                        """ if isinstance(option_text, list):
                            option_text  = option_text[0] """
                        if option_text != '':
                            o = Option(text=option_text ,
                                       Opnum=i, question_id=q)
                            o.question_id = q
                            o.save()
                            q.options.append(o)
                            q.save()
                except (KeyError, IndexError) as e:
                    pass

        # Committing changes after all modifications
        



        # Process the JSON data as needed
        # Respond with JSON (optional)
        ques_count = Question.objects(test_id=test_id).all()
        text = f"Total Question(s) is now {len(ques_count)}, Question data saved successfully"
        response_data = {'status': 'success', 'message': text}
        return JsonResponse(response_data, status=200)
    else:
        response_data = {'status': 'error', 'error': f'error saving question'}
        return JsonResponse(response_data, 200) 
    return jsonify({'status': 'error', 'message': 'Invalid request method'}), 400

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([])
def question_post_delete(request):
    base_url = os.path.dirname(os.path.abspath(__name__))
    # Handle the DELETE request
    # This example assumes 'hash' is a parameter passed in the request
    id = request.GET.get('hash', '')
    # Perform deletion logic based on the hash value
    # Adjust this part based on your specific requirements
    # Example: Delete the question with a specific hash
    uq = Userquestion.objects(question_id=id).first()
    if uq:
        return JsonResponse({'error': 'WARNING: The question has already been taken by applicants, cant be deleted'}, status=200)
    question = Question.objects(question_id=id).first()
    if question:
        opts = Option.objects(question_id=question).all()
        for opt in opts:
            opt.delete()
        ques = Question.objects(question_id=id).first()
        if ques is not None:
            try:
                imagstagjpeg = f"image_{ques.question_id}_{ques.test_id}.jpeg"
                imagstagjpg = f"image_{ques.question_id}_{ques.test_id}.jpg"
                imagstagpng = f"image_{ques.question_id}_{ques.test_id}.png"
                img_path1 = os.path.join(base_url, 'static/images', imagstagjpeg)
                img_path2 = os.path.join(base_url, 'static/images', imagstagjpg)
                img_path3 = os.path.join(base_url, 'static/images', imagstagpng)
                img_paths = [os.path.join(base_url, 'static', 'images', filename) for filename in (imagstagjpeg, imagstagjpg, imagstagpng)]

                imageurl = None
                for path in img_paths:
                    if os.path.exists(path):
                        os.remove(path)
                # k = [img_path1, img_path2, img_path3]
                # for path in k:
                #    if os.path.exists(path):
                #            os.remove(path)
            except:
                pass
            Test.objects.update(pull__questions=ques)
            ques.delete()
        #db.session.commit()
        return JsonResponse({'message': 'Question deleted sucessfully'}, status=200)
    return JsonResponse({'error': 'Nothing to delete'}, status=200)

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([])
def get_data(request, test_id, user_id):
    json_data = {}
    countquestion = 0
    q = Question.objects(test_id=test_id).order_by('Qnum')
    for question in q:
        countquestion += 1
        countOpt = 0
        id = question.question_id
        qu = f"question_text_{question.Qnum}-{id}"
        img = f"image_{question.question_id}"
        base_url = os.path.dirname(os.path.abspath(__name__))
        imagstagjpeg = f"image_{question.question_id}_{test_id}.jpeg"
        imagstagjpg = f"image_{question.question_id}_{test_id}.jpg"
        imagstagpng = f"image_{question.question_id}_{test_id}.png"
        img_path1 = os.path.join(base_url, 'static/images', imagstagjpeg)
        img_path2 = os.path.join(base_url, 'static/images', imagstagjpg)
        img_path3 = os.path.join(base_url, 'static/images', imagstagpng)

        if os.path.exists(img_path1):
            json_data[img] = imagstagjpeg
        elif os.path.exists(img_path2):
            json_data[img] = imagstagjpg
        elif os.path.exists(img_path3):
            json_data[img] = imagstagpng
        #json_data[img] = question.image_path
        json_data[qu] = question.text
        opts = Option.objects(question_id=question).order_by('Opnum')
        for option in opts:
            option_key = f"option_text_{question.Qnum}_{option.Opnum}"
            json_data[option_key] = option.text
        correct_key = f"correct_option_{question.Qnum}"
        lst = []
        if len(question.correct_answer) > 1:
            lst = question.correct_answer.split(',')
        else:
            lst.append(question.correct_answer)
        json_data[correct_key] = lst
        json_data['Lnum'] = question.Qnum
    return JsonResponse(json_data, status=200)

def save_file_to_disk(uploaded_file, directory, new_filename):
    os.makedirs(directory, exist_ok=True)  # Ensure directory exists
    file_path = os.path.join(directory, new_filename)

    with open(file_path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    return file_path

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([])
def uploadimages(request, test_id):
    base_url = os.path.dirname(os.path.abspath(__name__))
    ques = Question.objects(test_id=test_id).all()
    for q in ques:
        try:
            file_key = f'image_{q.question_id}_{test_id}'
            if file_key in request.FILES:
                file = request.FILES[file_key]
                if file and file.name:
                    file_extension = os.path.splitext(file.name)[1]
                    if file_extension == '.jpg' or file_extension == '.png' or file_extension == '.jpeg':
                        new_filename = f'image_{q.question_id}_{test_id}{file_extension}'
                        imagstagjpeg = f'image_{q.question_id}_{test_id}.jpeg'
                        imagstagpng = f'image_{q.question_id}_{test_id}.png'
                        imagstagjpg = f'image_{q.question_id}_{test_id}.jpg'
                        img_path1 = os.path.join(base_url, 'static/images', imagstagjpeg)
                        img_path2 = os.path.join(base_url, 'static/images', imagstagjpg)
                        img_path3 = os.path.join(base_url, 'static/images', imagstagpng)
                        k = [img_path1, img_path2, img_path3]
                        for path in k:
                            if os.path.exists(path):
                                    os.remove(path)
                        from django.conf import settings
                        base_dir = os.path.join(settings.BASE_DIR, 'static/images')
                        file_path = save_file_to_disk(file, base_dir, new_filename)
                        # Save the file with the new filename
                        # from django.core.files.base import ContentFile
                        # default_storage.save(os.path.join(base_url, 'static/images', new_filename), ContentFile(file.read()))

                    # Update the database with the new filename
        except Exception as e:
            print(f"Error processing file {file_key}: {str(e)}")
            continue
    response_data = {'status': 'success', 'message': 'Images uploaded successfully'}
    return JsonResponse(response_data, status=200)

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([])
def posttest_getquestions(request):
    data = json.loads(request.body)
    new = data['new_test_id']
    old = data['old_test_id']
    newtest = Test.objects(test_id=new).first()
    oldtest = Test.objects(test_id=old).first()
    from django.conf import settings
    base_url = settings.BASE_DIR
    # base_url = os.path.dirname(os.path.abspath(__name__))
    if len(oldtest.questions) <= 0:
        response_data = {
            'status': 'success',
            'message': 'No questions found for the selected test'
        }
        return JsonResponse(response_data, status=200)
    else:
        for ques in oldtest.questions:
            q = Question(test_id=newtest.test_id, question_id=str(uuid4()), text=ques.text, Qnum=ques.Qnum, correct_answer=ques.correct_answer)
            q.save()
            newtest.questions.append(q)
            newtest.save()
            q_options = Option.objects(question_id=ques).all()
            for op in q_options:
                o = Option(question_id=q, text=op.text, Opnum=op.Opnum)
                o.save()
                q.options.append(o)
                q.save()
            # Copy, rename, and move the image file
            imagetag = f"image_{ques.question_id}_{ques.test_id}"
            img_extensions = ['.jpeg', '.jpg', '.png']
            temp_dir = os.path.join(base_url, 'static', 'images','temp') # Update with your temporary directory path
            static_images_dir = os.path.join(base_url, 'static', 'images')

            for ext in img_extensions:
                img_path_src = os.path.join(static_images_dir, f"{imagetag}{ext}")
                if os.path.exists(img_path_src):
                    img_path_temp = os.path.join(temp_dir)
                    img_path_dst = os.path.join(static_images_dir)

                    # Copy the file to temporary directory
                    shutil.copy(img_path_src, img_path_temp)

                    # Rename the file based on new IDs
                    new_imagetag = f"image_{q.question_id}_{q.test_id}"
                    print(new_imagetag)
                    new_img_path_temp = os.path.join(temp_dir, f"{new_imagetag}{ext}")
                    os.rename( os.path.join(img_path_temp, f"{imagetag}{ext}") , new_img_path_temp)

                    # Move the renamed file back to static/images
                    shutil.move(new_img_path_temp, img_path_dst)

        response_data = {
            'status': 'success',
            'message': 'Questions imported successfully'
        }
        return JsonResponse(response_data, status=200)



@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def Addtestuser(request, test_id, user_id):
    test = Test.objects(test_id=test_id, userid=user_id).first()
    if test:
        return render(request, 'Addtestuser.html', {'test_id': test_id, 'user_id':user_id})
    return JsonResponse({'error': 'Unauthorized user'}, status=401)

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([])
def Addtestuserpost(request, test_id, user_id):
    user = User.objects.filter(userid=user_id).first()
    if not user:
        return JsonResponse({'error': 'Unauthorized user'}, status=401)
    timezone_ = request.session['timezone']
    if timezone_:
        activate(timezone_)
    com = Company.objects.filter(companyid=request.user.company_id).first()
    test = Test.objects(test_id=test_id).first()
    if not test:
        return JsonResponse({'error': 'Unauthorized user'}, status=401)
    question = Question.objects(test_id=test_id).first()
    if not question:
        return JsonResponse({'error': 'INFO: Please add questions to the test, before your proceed'}, status=200)
    j = json.loads(request.body)
    input_date = j.get('date', '')
    input_time = j.get('time', '')
    count = j.get('count', '')
    duration = j.get('duration', '')
    formatted_datetime = validate_and_format_datetime(input_date, input_time)
    if  make_aware(formatted_datetime) < timezone.localtime(timezone.now()):
        return JsonResponse({'message': 'Date/Time is in the past'}, status=401)
    teststat = Teststat.objects(test_id=test, test_date=formatted_datetime).first()
    if not teststat:
        teststat =  Teststat(test_day_id= str(uuid4()),test_date= formatted_datetime, duration=duration)
        teststat.test_id = test
        teststat.save()
        test.teststats.append(teststat)
        test.save()
    for i in range(1, count + 1):
        fullname = j.get(f'user_{i}', '')['username']
        email = j.get(f'user_{i}', '')['email']
        applicant = Applicanttest.objects(test_day_id=teststat, user_email=email).first()
        if not applicant:
            applicant = Applicanttest(secret_key=str(uuid4())[-9:], user_id=str(uuid4())[-9:],
                                      test_day_id=teststat, user_email=email,
                                      start_date=None, fullname=fullname)
            applicant.save()
            teststat.applicanttests.append(applicant)
            teststat.save()
            try:
                run_time = datetime.datetime.now() + datetime.timedelta(seconds=10) 
                # send_applicantmail(email, fullname, formatted_datetime, duration, test.test_name, 'sample company', 'Test lab',
                #                user.emaill, user.first_name, applicant.user_id, applicant.secret_key)
                scheduler.add_job(id=f'send_applicantmail{applicant.user_id}', func=send_applicantmail, args=(email, fullname, formatted_datetime, duration, test.test_name, com.company_name, com.company_address,
                                user.email, user.first_name, applicant.user_id, applicant.secret_key), trigger='date', run_date=run_time)
                
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
                #return jsonify({'error': 'Mail sending error, check for incorrect email address and try again'})
    return JsonResponse({'message': 'Email Sent successfully'}, status=200)



@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def testlist(request, test_id):
    """test list."""
    count = 1
    start_date = ''
    end_date = ''
    ed = None
    sd = None
    du = None
    q_param = request.GET.get('q')
    test = Test.objects(test_id=test_id).first()
    if not test:
        return JsonResponse({'error': 'Unauthorized User'}, status=401)
    if q_param == 'date' and request.data.get('start-date') != '' and request.data.get('end-date') != '':
        start_date = datetime.datetime.strptime(request.data.get('start-date'), '%Y-%m-%d')
        end_date = datetime.datetime.strptime(request.data.get('end-date'), '%Y-%m-%d')
        duration = request.data.get('duration')
        if duration == '':
            duration = 0
        teststat_queryset = Teststat.objects(test_id=test) \
                    .filter(
                        test_date__gte=start_date,
                        test_date__lte=end_date,
                        duration=int(duration)
                    ) \
                    .order_by('-test_date')
        sd = request.data.get('start-date')
        ed = request.data.get('end-date')
        du = request.data.get('duration')
    else:
        teststat_queryset = Teststat.objects(test_id=test).order_by('test_date')
    # if not teststat_queryset:
    #    return JsonResponse({'error': 'Unauthorized User'}, status=401)
    page_number = request.GET.get('page', 1)
    # Ensure the page number is a valid positive integer
    if int(page_number) <= 1:
        page_number = 1  # Fallback to the first page if the page number is invalid
    paginator = Paginator(teststat_queryset, 3)  # 3 items per page
    try:
        pages = paginator.page(page_number)
    except EmptyPage:
        # If the requested page number is out of range, show the last page
        pages = paginator.page(paginator.num_pages) 
    
    return render(request, 'Testlist.html', {'teststat': teststat_queryset, 'i': 0, 'pages': pages,
                           'test_id': test_id, 'testname': test.test_name, 'user_id': test.userid, 'sd': sd, 'ed': ed, 'du': du})

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def deletemaintest(request, test_id):
    data = json.loads(request.body)
    test_id = data['test_id']
    test = Test.objects(test_id=test_id).first()
    if test:
        from django.conf import settings
        Q = Question.objects(test_id=test_id).all()
        if Q:
            base_url = settings.BASE_DIR
            for q in Q:
                uq = Userquestion.objects(question_id=q.question_id).all()
                if uq:
                    for uu in uq:
                        uu.delete()
                q_options = Option.objects(question_id=q).all()
                for o in q_options:
                    o.delete()
                imagstagjpeg = f'image_{q.question_id}_{test_id}.jpeg'
                imagstagpng = f'image_{q.question_id}_{test_id}.png'
                imagstagjpg = f'image_{q.question_id}_{test_id}.jpg'
                img_path1 = os.path.join(base_url, 'static/images', imagstagjpeg)
                img_path2 = os.path.join(base_url, 'static/images', imagstagjpg)
                img_path3 = os.path.join(base_url, 'static/images', imagstagpng)
                img_paths = [os.path.join(base_url, 'static', 'images', filename) for filename in (imagstagjpeg, imagstagjpg, imagstagpng)]

                imageurl = None
                for path in img_paths:
                    if os.path.exists(path):
                        os.remove(path)
                # k = [img_path1, img_path2, img_path3]
                # for path in k:
                #    if os.path.exists(path):
                #         os.remove(path)
                Test.objects.update(pull__questions=q)
                q.delete()
        teststat = Teststat.objects(test_id=test).all()
        if teststat:
            for t in teststat:
                for app in t.applicanttests:
                    app.delete()
                t.delete()
        test.delete()
        # t = Test.query.filter_by(userid=user_id).all()
        return JsonResponse({'message': 'All test records have been deleted', 'status': 'success'}, status=200)
    return JsonResponse({'message': 'An error occured while performing this operation','status': 'error, not a valid test'}, status=200)




@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def rescheduletestpost(request, test_day_id):
    # Get the date and time from the POST request
    # Get the JSON data from the POST request
    data = json.loads(request.body)

    # Access the 'date' and 'time' fields from the JSON data
    input_date = data.get('date')
    input_time = data.get('time')
    if input_date is None or input_time is None:
        return JsonResponse({'error': 'Date or time is missing'}, status=400)

    # Validate and format the datetime
    formatted_datetime = validate_and_format_datetime(input_date, input_time)

    if formatted_datetime is None:
        return JsonResponse({'error': 'Invalid date or time format'}, 400)
    
    if formatted_datetime < datetime.datetime.today():
        # flash('Datetime should be in the future or todays date')
        return JsonResponse({'error': 'Datetime should be in the future or todays date'}, status=200)
        #return redirect(url_for('rescheduletestget', test_day_id=test_day_id))
    # At this point, 'formatted_datetime' is a valid datetime
    # Save it to the database (replace this with your actual database saving logic)
    ts = Teststat.objects(test_day_id=test_day_id).first()
    if ts.status == 'taken':
          return JsonResponse({'error': 'Test already taken, cant be rescheduled'}, status=200)
    if ts.status != 'taken':
        test = Test.objects(test_id=ts.test_id.test_id).first()
        ts.test_date = formatted_datetime
        ts.save()
        applicants = Applicanttest.objects(test_day_id=ts, test_status='pending').all()
        for a in applicants:
            run_time = datetime.datetime.now() + datetime.timedelta(seconds=10) 
            scheduler.add_job(id=f'send_reschedule_mail{a.user_id}', func=send_reschedule_mail, args=(a.fullname, formatted_datetime, test.test_name , a.user_email), trigger='date', run_date=run_time)        
        # Return a success response
        # return redirect(url_for('rescheduletestget', test_day_id=test_day_id))
    return JsonResponse({'message': 'Test Rescheduled successfully'}, status=200)

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def rescheduletestget(request, test_day_id):
    teststat = Teststat.objects(test_day_id=test_day_id).first()
    if teststat:
        test = Test.objects(test_id=teststat.test_id.test_id).first()
        return render(request, 'rescheduletest.html',
                            {'test_day_id': test_day_id, 'testname':test.test_name, 'test_id':test.test_id})
    else:
        return JsonResponse({'error': 'Unauthorized User'}, status=401)

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def resendmailget(request, test_day_id, user_id):
    teststat = Teststat.objects(test_day_id=test_day_id).first()
    if not teststat:
        return JsonResponse({'error': 'Unauthorized user'}, status=200)
    return render(request, 'Resendemail.html', {'test_id':teststat.test_id.test_id, 'test_day_id':test_day_id, 'user_id':user_id})

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([])
def resendmailpost(request, test_day_id, user_id):
    user = User.objects.filter(userid=user_id).first()
    if not user:
        return JsonResponse({'error': 'Unauthorized user'}, status=401)
    com = Company.objects.filter(companyid=request.user.company_id).first()
    teststat = Teststat.objects(test_day_id=test_day_id).first()
    if not teststat:
        return JsonResponse({'error': 'Unauthorized user'}, status=401)
    test = Test.objects(test_id=teststat.test_id.test_id).first()
    j = json.loads(request.body)
    count = j.get('count', 0)
    for i in range(1, count + 1):
        fullname = j.get(f'user_{i}', '')['username']
        email = j.get(f'user_{i}', '')['email']
        applicant = Applicanttest.objects(test_day_id=teststat, user_email=email).first()
        if not applicant:
            applicant = Applicanttest(secret_key=str(uuid4())[-9:], user_id=str(uuid4())[-9:],
                                      test_day_id=teststat, user_email=email,
                                      start_date=None, fullname=fullname)
            applicant.save()
            teststat.applicanttests.append(applicant)
            teststat.save()
            try:
                # send_applicantmail(email, fullname, teststat.test_date, teststat.duration, test.test_name, 'sample company', 'Test lab',
                                # user.email, user.first_name, applicant.user_id, applicant.secret_key)
                run_time = datetime.datetime.now() + datetime.timedelta(seconds=10) 
                # send_applicantmail(email, fullname, formatted_datetime, duration, test.test_name, 'sample company', 'Test lab',
                #                user.email, user.first_name, applicant.user_id, applicant.secret_key)
                scheduler.add_job(id=f'send_applicantmail{datetime.datetime.now()}', func=send_applicantmail, args=(email, fullname, teststat.test_date, teststat.duration, test.test_name, com.company_name, com.company_address,
                                user.email, user.first_name, applicant.user_id, applicant.secret_key), trigger='date', run_date=run_time)

            except:
                return JsonResponse({'error': 'Mail sending error, check internet connection or check incorrect email address and try again'}, status=200)
    return JsonResponse({'message': 'Saved successfully'}, status=200)

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([])
def deletetestday(request, test_day_id):
    teststat = Teststat.objects(test_day_id=test_day_id).first()
    if teststat:
        if teststat.status != 'pending':
            return JsonResponse({'error': 'WARNING: Test has been taken, cannot be deleted'}, status=200)
        test = Test.objects(test_id=teststat.test_id.test_id).first()
        applicants = Applicanttest.objects(test_day_id=teststat, test_status='pending').all()
        for a in applicants:
            run_time = datetime.datetime.now() + datetime.timedelta(seconds=10) 
            scheduler.add_job(id=f'send_canceltest_mail{a.user_id}', func=send_canceltest_mail, args=(a.fullname, test.test_name , a.user_email), trigger='date', run_date=run_time)        

    applicant = Applicanttest.objects(test_day_id=teststat).all()
    if applicant:
        for ap in applicant:
            Teststat.objects.update(pull__applicanttests=ap)
            ap.delete()
    teststat = Teststat.objects(test_day_id=test_day_id).first()
    if teststat:
        teststat.delete()
        Test.objects.update(pull__teststats=teststat)
        return JsonResponse({'message': 'Test deleted successfully'}, status=200)
    else:
         return JsonResponse({'error': 'Unauthorized User'}, status=401)

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([])
def testsummary(request, test_id, test_day_id, user_id):
    test = Test.objects(test_id=test_id).first()
    teststat = Teststat.objects(test_day_id=test_day_id).first()
    user = User.objects.filter(userid=user_id).first()

    if not test or not teststat or not user:
        return JsonResponse({'error': 'Unauthorized user'}, status=401)

    
    allapplicants = Applicanttest.objects(test_day_id=teststat)\
                                        .order_by('-score').all()
    applicant_data = []

    for app in allapplicants:
        correct_answers = 0
        questions_data = []
        status = 'Not attempted'
        user_questions = Userquestion.objects(user_id=app.user_id).all()
        qcount = len(user_questions)
        for uq in user_questions:
            if status == 'Not attempted':
                status = 'Completed'
            ques = Question.objects(question_id=uq.question_id).first()
            if ques:
                imageurl = None
                #base_url = os.path.dirname(os.path.abspath(__name__))
                from django.conf import settings
                base_url = settings.BASE_DIR
                imagstagjpeg = f'image_{ques.question_id}_{test.test_id}.jpeg'
                imagstagpng = f'image_{ques.question_id}_{test.test_id}.png'
                imagstagjpg = f'image_{ques.question_id}_{test.test_id}.jpg'
                img_path1 = os.path.join(base_url, 'static/images', imagstagjpeg)
                img_path2 = os.path.join(base_url, 'static/images', imagstagjpg)
                img_path3 = os.path.join(base_url, 'static/images', imagstagpng)
                img_paths = [os.path.join(base_url, 'static', 'images', filename) for filename in (imagstagjpeg, imagstagjpg, imagstagpng)]

                imageurl = None
                for path in img_paths:
                    if os.path.exists(path):
                        imageurl = path.replace(base_url, '').replace('\\', '/')  # Adjust path separator for Windows
                        break

                # print(imageurl)
                # k = [img_path1, img_path2, img_path3]
                # for path in k:
                #    if os.path.exists(path):
                #        path = path.split('/')[1:]
                #        # imageurl = '/' + path[1] + '/' + path[2] + '/' + path[3]
                #        print(imageurl)
                #        break
                question_text = ques.text
                question_point = 0
                if sorted(uq.answer_chosen) == sorted(ques.correct_answer):
                    correct_answers += 1
                    question_point = 1
                questions_data.append({'text': question_text, 'point': question_point, 'imageurl': imageurl})
        applicant_data.append({
            'name': app.fullname,
            'email': app.user_email,
            'score': f'{app.score}%',
            'status': status,
            'questions': questions_data,
            'marks': f'{correct_answers}/{qcount}'
        })
    return render(request, 'Testsummary.html', {'testname=':test.test_name, 'test_id':test_id
                           ,'test_day_id':test_day_id, 'user_id':user_id,  'applicants':applicant_data, 'count':len(allapplicants)})



@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def applicant(request, test_day_id):
    teststat = Teststat.objects(test_day_id=test_day_id).first()
    if teststat:
        return render(request, 'applicant.html', {'duration':teststat.duration})
    return JsonResponse({'error': 'cant load page'}, status=200)


@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([])
def authenticate_applicant(request, user_id, secret_key):
    timezone_ = request.session['timezone']  # Store in session
    if timezone_:
        activate(timezone_)
    applicant = Applicanttest.objects(user_id=user_id).first()
    if not applicant:
        return JsonResponse({'error': 'Unauthorized User'}, status=200)
    teststat = Teststat.objects(test_day_id=applicant.test_day_id.test_day_id).first()
    if timezone.localtime(timezone.now()) < make_aware(teststat.test_date):
        return JsonResponse({'error': 'Test hasnt been approved yet'}, status=200)
    expires_in = datetime.timedelta(days=1)
    user_id = user_id + secret_key
    student = Applicanttest.objects(secret_key=secret_key).first()
    #access_token = create_access_token(user_id, expires_in)
    #AccessToken.set_exp(expires_in)
    access_token = AccessToken.for_user(student)
    access_token.set_exp = expires_in
    # Set the JWT token as a cookie
    # response = jsonify(access_token=access_token)
    #response.set_cookie('UserTestToken', value=access_token, httponly=False, secure=True, path='/', samesite='Strict')  # Adjust secure=True based on your deployment
    # return response
    #response = JsonResponse(access_token=access_token)
    #response.set_cookie('UserTestToken', value=access_token, httponly=False, secure=False, path='/')

    # Make the response with the cookie
    #return make_response(response, 200)
    response = Response({'message': 'Login successful', 'access_token': str(access_token)}, status=status.HTTP_200_OK)
    response.set_cookie('UserTestToken', value=str(access_token), httponly=False, secure=False, samesite='Lax')
    return  response


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def taketest(request, user_id, key):
    #remember to set this token on the start page for the test
    # an api will veryfy the access token then open the main 
    # test page
    timezone_ = request.session['timezone']  # Store in session
    if timezone_:
        activate(timezone_)
    applicant = Applicanttest.objects(user_id=user_id).first()
    if not applicant:
        return JsonResponse({'error': 'Unauthorized User'}, status=401)
    teststat = Teststat.objects(test_day_id=applicant.test_day_id.test_day_id).first()
    if  timezone.localtime(timezone.now()) < make_aware(teststat.test_date):
        return JsonResponse({'error': 'Test hasnt been approved yet'}, status=200)
    if applicant and applicant.test_status == 'completed':
        #redirect_url = url_for()
        return redirect('Timeout', test_day_id=applicant.test_day_id, user_id=applicant.user_id)
    if user_id == applicant.user_id and key == applicant.secret_key:
        # Set a custom expiration time (e.g., 7 days)
        #expires_in = timedelta(days=1)
        #access_token = create_access_token(user_id, expires_in)
        # Set the JWT token as a cookie
        #response = jsonify(access_token=access_token)
        #response.set_cookie('UserTestToken', value=access_token, httponly=False, secure=True, path='/', samesite='Strict')  # Adjust secure=True based on your deployment
        #sreturn response
        if applicant.started != 'True':
            applicant.started = True
        if not applicant.start_date:
            applicant.start_date = timezone.localtime(timezone.now())
        applicant.save()
        return render(request, 'taketest.html', {'test_day_id':teststat.test_day_id,
                               'user_id':user_id, 'test_id':teststat.test_id.test_id})
    else:
        return JsonResponse({'error': 'Not Authorized'}, status=200)  

def convert_to_local(utc_time, timezone):
    # Create a timezone object for the given timezone
    local_tz = pytz.timezone(timezone)
    # Convert UTC time to the local time zone
    return utc_time.astimezone(local_tz)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def get_question(request, question_num, test_day_id, user_id):
    # Check if the question number exists in the data
    timezone_ = request.session['timezone']
    if timezone_:
        activate(timezone_)
    appcheck = Applicanttest.objects(user_id=user_id, test_status='completed' ).first()
    if appcheck:
        return render(request, 'Timeout.html', {'test_day_id':test_day_id})
    test = Teststat.objects(test_day_id=test_day_id).first()
    applicantdata = Applicanttest.objects(user_id=user_id).first()
    if not applicantdata:
        return JsonResponse({'error': 'user not found'}, status=404)
    cur_time = timezone.localtime(timezone.now())  # Localized current time
    time_span = datetime.timedelta(seconds=(test.duration * 60) + 8)
    exp_time = convert_to_local(applicantdata.start_date, timezone_) + time_span  # Already aware

    # Ensure exp_time is aware if it isn't already
    if is_naive(exp_time):
        exp_time = make_aware(exp_time)

    if exp_time < cur_time:
        print('Test Expired')
        return JsonResponse({'message': 'Test Expired'}, status=200)
    Ques_data = {'options': {}}  # Initialize options as an empty dictionary
    #Ques_data['duration'] = cur_time - exp_time
    Ques_data['selectedOptions'] = []
    user_question = Userquestion.objects(user_id=user_id, Qnum=question_num).first()
    if user_question:
        if len(user_question.answer_chosen) == 1:
             Ques_data['selectedOptions'] = [user_question.answer_chosen]
        else:
            Ques_data['selectedOptions'] = user_question.answer_chosen.split(',')
    
    print(test.test_id.test_id)
    print(question_num)
    question = Question.objects(Qnum=question_num, test_id=test.test_id.test_id).first()
    if question:
        from django.conf import settings
        base_url = settings.BASE_DIR
        imagstagjpeg = f'image_{question.question_id}_{test.test_id}.jpeg'
        imagstagpng = f'image_{question.question_id}_{test.test_id}.png'
        imagstagjpg = f'image_{question.question_id}_{test.test_id}.jpg'
        img_path1 = os.path.join(base_url, 'static/images', imagstagjpeg)
        img_path2 = os.path.join(base_url, 'static/images', imagstagjpg)
        img_path3 = os.path.join(base_url, 'static/images', imagstagpng)
        img_paths = [os.path.join(base_url, 'static', 'images', filename) for filename in (imagstagjpeg, imagstagjpg, imagstagpng)]
        imageurl = None
        for path in img_paths:
            if os.path.exists(path):
                Ques_data['imageurl'] = path.replace(base_url, '').replace('\\', '/')  # Adjust path separator for Windows
                break
        # k = [img_path1, img_path2, img_path3]
        # for path in k:
        #    if os.path.exists(path):
        #        path = path.split('/')[1:]
        #        Ques_data['imageurl'] = '/' + path[1] + '/' + path[2] + '/' + path[3] 
        #        break
        Ques_data['Question'] = question.text
        Ques_data['question_id'] = question.question_id
        # Retrieve options and sort by Opnum in ascending order
        options = Option.objects(question_id=question).order_by('Opnum').all()

        for option in options:
            Ques_data['options'][option.Opnum] = option.text

        return JsonResponse(Ques_data, status=200, safe=False)
    else:
        return JsonResponse({'error': 'Question not found'}, status=404)


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def question_count(request, test_day_id, user_id):
    timezone_ = request.session['timezone']
    if timezone_:
        activate(timezone_)
    test = Teststat.objects(test_day_id=test_day_id).first()
    applicantdata = Applicanttest.objects(user_id=user_id).first()
    if not applicantdata:
        return JsonResponse({'error': 'user not found'}, status=404)
    cur_time = timezone.localtime(timezone.now())
    time_span = datetime.timedelta(seconds=(test.duration  * 60) + 8)
    exp_time = convert_to_local(applicantdata.start_date, timezone_) + time_span
    if is_naive(exp_time):
        exp_time = make_aware(exp_time)
    if exp_time < cur_time:
        return JsonResponse({'message': 'Test Expired'}, status=200)
    
    question =  Question.objects(test_id=test.test_id.test_id).all()
    if question:
        #cur_time = datetime.now()
        #time_span = timedelta(seconds=test.duration)
        #duration = session_dict['created_at'] + time_span
        #if exp_time < cur_time:
        print((((exp_time - cur_time).total_seconds() + 1)/60))
        return JsonResponse({'count': len(question), 'duration': (((exp_time - cur_time).total_seconds() + 1)/60)}, status=200)
    else:
        return JsonResponse({'error': 'Question not found'}, status=404)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def post_selection(request):
    timezone_ = request.session['timezone']
    if timezone_:
        activate(timezone_)
    json_data = json.loads(request.body)
    if not json_data:
        return Response(JsonResponse({'error': 'Not a JSON'}, status=400)) 
    else:
        userId = json_data['user_id']
        appcheck = Applicanttest.objects(user_id=userId, test_status='completed' ).first()
        if appcheck:
            return render(request, 'Timeout.html', {})
        currentQuestionId = json_data['question_id']
        selectedOptions = json_data['option_numbers']
        question_number = int(json_data['question_number'])
        user_question = Userquestion.objects(question_id=currentQuestionId, user_id=userId).first()
        correct_str = ''
        for c in range(len(selectedOptions)):
            if c < len(selectedOptions) - 1:
                correct_str += selectedOptions[c] + ','
            else:
                correct_str += selectedOptions[c] 
        if user_question:
            user_question.created_date = timezone.localtime(timezone.now())
            #user_question.answer_chosen = selectedOption
            user_question.answer_chosen = correct_str
            user_question.save()
            return JsonResponse({'message': 'posted'}, status=200)  
        else:
            user_question = Userquestion(created_date=timezone.localtime(timezone.now()),question_id=currentQuestionId,
                                         Qnum=question_number,
                                         user_id=userId,
                                         answer_chosen=correct_str)
            user_question.save()
            return JsonResponse({'message': 'posted'}, status=200)  

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def Timeout(request, test_day_id, user_id):
    timezone_ = request.session['timezone']
    if timezone_:
        activate(timezone_)
    questioncount = 0
    correct_answers = 0
    applicant = Applicanttest.objects(user_id=user_id).first()
    if not applicant:
        return JsonResponse({'error': 'Unauthorized User'}, status=200)
    if applicant and applicant.test_status == 'pending':
        teststat = Teststat.objects(test_day_id=test_day_id).first()
        if teststat:
            test = Test.objects(test_id=teststat.test_id.test_id).first()
            if test:
                questioncount = len(test.questions)
                user_questions = Userquestion.objects(user_id=user_id).all()
                # Count the number of correct answers
                for uq in user_questions:
                    ques = Question.objects(question_id=uq.question_id).first()
                    if ques:
                        if sorted(uq.answer_chosen) == sorted(ques.correct_answer):
                            correct_answers += 1
                questions = Question.objects(test_id=teststat.test_id.test_id).all()
                for question in questions:
                    u = Userquestion.objects(question_id=question.question_id, user_id=user_id).first()
                    if not u:
                        user_question = Userquestion(question_id=question.question_id,
                                        Qnum=question.Qnum,
                                        created_date=timezone.localtime(timezone.now()),
                                        user_id=user_id,
                                        answer_chosen='')
                        user_question.save()
                        
                            
                # Calculate the percentage score
                percentage_score = (correct_answers / questioncount) * 100

                # Round the percentage to two decimal places
                percentage_score = round(percentage_score, 2)
                applicant.score = percentage_score
                applicant.test_status = 'completed'
                if teststat.status != 'taken':
                    teststat.status = 'taken'
                applicant.save()
                teststat.save()
                try:
                    run_time = timezone.localtime(timezone.now()) + datetime.timedelta(seconds=10) 
                    scheduler.add_job(id=f'send_test_mail{user_id}', func=send_test_mail, args=(test_day_id, user_id), trigger='date', run_date=run_time)
                except:
                    return JsonResponse({'message': 'INFO: An error occured while sending mail to ' + applicant.user_email + 'please try again or check that the email is correct'}, status=200)

                # send_test_mail(test_day_id, user_id)
    return render(request, 'Timeout.html', {'test_day_id':test_day_id})


@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def emailboard(request, user_id):
    count = 1
    u = User.objects.filter(userid=user_id).first()
    if not u:
        return JsonResponse({'error': 'Unauthorized User'}, status=401)
    if u.role == 'user':
        return JsonResponse({'error': 'Unauthorized User'}, status=401)
    email = Emailserver.objects.all().order_by('-id')
    if not email:
        pass
        # If 'q_param' is not 'name' or 'name' is empty, filter by email exclusion and order by created
    email_queryset =  Emailserver.objects.all().order_by('-id')

    # Get the page number from the GET request, default to 1 if not specified
    page_number = request.GET.get('page', 1)

    # Ensure the page number is a valid positive integer
    if int(page_number) <= 1:
        page_number = 1  # Fallback to the first page if the page number is invalid

    paginator = Paginator(email_queryset, 3)  # 3 items per page

    try:
        pages = paginator.page(page_number)
    except EmptyPage:
        # If the requested page number is out of range, show the last page
        pages = paginator.page(paginator.num_pages)  # Get last page in case of out-of-range page

    return render(request, 'Emaildashboard.html', {
        'email': email_queryset,
        'companyname':'',
        'pages': pages,
          'i': 0,
        'user_id': user_id
    })

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def computescore(request, test_day_id):
    timezone_ = request.session['timezone']
    if timezone_:
        activate(timezone_)
    teststat = Teststat.objects(test_day_id=test_day_id).first()
    if not teststat:
        return JsonResponse({'error': 'Unauthorized User'}, status=401)
    applicants = Applicanttest.objects(test_day_id=teststat, test_status='pending').all()
    for applicant in applicants:
        correct_answers = 0
        if applicant and applicant.test_status == 'pending':
            teststat = Teststat.objects(test_day_id=test_day_id).first()
            if teststat:
                test = Test.objects(test_id=teststat.test_id.test_id).first()
                if test:
                    questioncount = len(test.questions)
                    user_questions = Userquestion.objects(user_id=applicant.user_id).all()
                    # Count the number of correct answers
                    for uq in user_questions:
                        ques = Question.objects(question_id=uq.question_id).first()
                        if ques:
                            if sorted(uq.answer_chosen) == sorted(ques.correct_answer):
                                correct_answers += 1
                    questions = Question.objects(test_id=teststat.test_id.test_id).all()
                    for question in questions:
                        u = Userquestion.objects(question_id=question.question_id, user_id=applicant.user_id).first()
                        if not u:
                            user_question = Userquestion(created_date=timezone.localtime(timezone.now()), question_id=question.question_id,
                                            Qnum=question.Qnum,
                                            user_id=applicant.user_id,
                                            answer_chosen='')
                            user_question.save()
                            
                                
                    # Calculate the percentage score
                    percentage_score = (correct_answers / questioncount) * 100

                    # Round the percentage to two decimal places
                    percentage_score = round(percentage_score, 2)
                    applicant.score = percentage_score
                    applicant.test_status = 'completed'
                    if teststat.status != 'taken':
                        teststat.status = 'taken'
                        teststat.save()
                    applicant.save()
                    try:
                        run_time = datetime.datetime.now() + datetime.timedelta(seconds=10) 
                        scheduler.add_job(id=f'send_test_mail{test_day_id}', func=send_test_mail, args=(test_day_id, applicant.user_id), trigger='date', run_date=run_time)
                        # send_test_mail(test_day_id, applicant.user_id)
                    except:
                        return JsonResponse({'message': 'INFO: An error occured while sending mail to ' + applicant.user_email + 'please try again or check that the email is correct'}, status=200)
    return JsonResponse({'message': 'All Scores computed successlfully'}, status=200)


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def updatemailstatus(request):
    direction = json.loads(request.body)
    if direction['direction'] == 'onchange':
        M = Emailserver.objects.all()
        if M:
            checked = False
            if M[0].active == 'No':
                M[0].active = 'Yes'
            else:
                M[0].active = 'No'
                checked = True
            M[0].save()
            return JsonResponse({'status': 'success', 'message':'Mail settings updated', 'checked': checked}, status=200)
        else:
            return JsonResponse({'status': 'error', 'error':'No record found'}, status=200)
    else:
        M = Emailserver.objects.all()
        if M:
            if M[0].active == 'Yes':
                return JsonResponse({'status': 'success', 'checked': False}, status=200)
            else:
                return JsonResponse({'status': 'success', 'checked': True}, status=200)
        else:
            return JsonResponse({'status': 'error'}, status=200)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def deletemail(request, email_id):
    data = json.loads(request.body)
    if data:
        M = Emailserver.objects.filter(emailid=email_id).first()
        if M:
            M.delete()
            return JsonResponse({'message': 'All records deleted', 'status': 'success'}, status=200)
    return JsonResponse({'message': 'An error occured while performing this operation','status': 'error, not a valid test'}, status=500)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def get_profile(reequest, user_id):
    M = User.objects.filter(userid=user_id).first()
    json_data = {}
    if M:
        json_data['firstName'] = M.first_name
        json_data['lastName'] =  M.last_name
        json_data['email'] = M.email
        json_data['status'] = 'success'
        json_data['message'] = 'success'
        return  JsonResponse(json_data, status=200)
    else:
         json_data['eror'] = 'success'
         json_data['message'] = 'An error Occured, couldnt retrieve your profile'
         return  JsonResponse(json_data, status=500)


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def get_mail(request, email_id):
    M = Emailserver.objects.filter(emailid=email_id).first()
    json_data = {}
    if M:
        json_data['sender'] = M.sender
        json_data['cc'] =  M.cc
        json_data['server'] = M.mail_server
        json_data['port'] = M.mail_port
        json_data['TLS'] = M.mail_use_tls
        json_data['SSL'] = M.mail_use_ssl
        json_data['SSL'] = M.mail_use_ssl
        json_data['username'] = M.username
        json_data['password'] = M.password
        json_data['status'] = 'success'
        json_data['message'] = 'success'
        return  JsonResponse(json_data, status=200)
    else:
         json_data['eror'] = 'success'
         json_data['message'] = 'An error Occured, couldnt retrieve user data'
         return  JsonResponse(json_data, status=500)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def savemail(request, user_id):
    try:
        data = json.loads(request.body)
        sender = data.get('sender', '')
        cc = data.get('cc', '')
        pwd = data.get('password', '')
        un = data.get('username', '')
        port = data.get('port', '')
        server = data.get('server', '')
        tls = data.get('TLS', '')
        mod = data.get('mod', '')
        ssl = data.get('SSL', '')
        
        modemailid = data.get('modemailid', '')

        user = User.objects.filter(userid=user_id).first()
        # Perform necessary operations with the test_name and user_id
        if user and mod != True:
            status = ''
            mails = Emailserver.objects.all()
            if len(mails) > 0:
                response_data = {
                'status': 'error',
                'error': 'Mail server already saved, you can only have one mail server settings'
            }
                return JsonResponse(response_data, status=200)
            
            if len(mails) == 0:
                status = 'Yes'
            else:
                status = 'No'
            Mail_ = Emailserver(sender=sender,
                            cc=cc,
                            emailid=str(uuid4()),
                            mail_server=server,
                            mail_use_ssl=ssl,
                            mail_use_tls=tls,
                            mail_port=port,
                            username=un,
                            password=pwd,
                            active=status)
            
            Mail_.save()
            response_data = {
                'status': 'success',
                'message': 'Mail saved successfully'
            }

            return JsonResponse(response_data,  status=200)
        else:
            u = Emailserver.objects.filter(emailid=modemailid).first()
            if u:
                u.sender = sender
                u.cc = cc
                u.mail_server = server
                u.mail_port = port
                u.mail_use_tls = tls
                u.mail_use_ssl = ssl
                u.username = un
                u.password = pwd
                u.save()
            
        # On success, you can send a response to refresh the current page
            response_data = {
                'status': 'success',
                'message': 'Mail saved successfully'
            }

            return JsonResponse(response_data, status=200)

    except Exception as e:
        # Handle any exceptions or errors
        error_data = {
            'status': 'error',
            'error': str(e)
        }

        return JsonResponse(error_data, status= 500)
@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def testmail(request, email_id, user_id):
    try:
        M = Emailserver.objects.filter(emailid=email_id).first()
        if M:
            EMAIL_HOST = M.mail_server
            EMAIL_PORT = M.mail_port
            EMAIL_USE_TLS = M.mail_use_tls
            # app.config['MAIL_USE_SSL'] = M.mail_use_ssl
            EMAIL_HOST_USER = M.username
            EMAIL_HOST_PASSWORD = M.password
            user = User.objects.filter(userid=user_id).first()
            if user:
                 email_message = EmailMessage(
            subject='MAIL TESTING SUCCESSFUL',
            body=f"Hi {user.last_name},\n\nThis is to inform you that your mail setting was accepted. \n\nRegards,\n\nTestCompanion team. ",
            from_email=M.sender, to=[M.cc, M.sender]
        )
            try:
                email_message.send()
                response_data = {
                    'status': 'success',
                    'message': 'Your settings is ok, Your test mail has been sent successfully'
                }
                return JsonResponse(response_data, status=200)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'message': 'wrong mail user'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'An error occured, please check your mail settings !!  {str(e)}', 'status': 'error'})

@csrf_exempt
@login_required
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def profileboard(request, user_id):
    user = User.objects.filter(userid=user_id).first()
    if user:
        com = Company.objects.filter(companyid=user.company_id).first()
        return render(request, 'profiledashboard.html',{
                               'companyname':com.company_name,
                               'addr':com.company_address,
                               'com_email':com.company_email,
                               'email':user.email,
                               'web':com.company_website,
                               'fn':user.first_name,
                               'ln':user.last_name,
                               'role':user.role,
                               'user_id':user_id})
    return JsonResponse({'error': f'An error occured', 'status': 'error'}, status=400)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def get_company(request, user_id):
    M = User.objects.filter(userid=user_id).first()
    json_data = {}
    if M:
        com = Company.objects.filter(companyid=M.company_id).first()
        if com:
            json_data['companyName'] = com.company_name
            json_data['companyWebsite'] = com.company_website
            json_data['companyEmail'] = com.company_email
            json_data['companyAddress'] = com.company_address
            json_data['status'] = 'success'
            json_data['message'] = 'success'
            return  JsonResponse(json_data, status=200)
        else:
            json_data['eror'] = 'success'
            json_data['message'] = 'An error Occured, couldnt retrieve company profile'
            return  JsonResponse(json_data, status=500)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def savecompany(request, user_id):
    try:
        data = json.loads(request.body)
        companyName = data.get('companyName', '')
        companyWebsite = data.get('companyWebsite', '')
        companyEmail = data.get('companyEmail', '')
        companyAddress = data.get('companyAddress', '')
        com = Company.objects.filter(companyid=request.user.company_id).first()
        if com:
            com.company_name = companyName
            com.company_website = companyWebsite
            com.company_address = companyAddress
            com.company_email = companyEmail
            com.save()
            response_data = {
                'status': 'success',
                'message': 'Company profile updated successfully'
            }
            return JsonResponse(response_data, status=200)
        else:
            response_data = {
                'status': 'error',
                'message': 'Unauthorized access',
                'error': 'Unauthorized access'
            }
            return JsonResponse(response_data, status=200)
    except:
        response_data = {
                'error': 'An error ocured while trying to save the profile',
                'message': 'error'
            }
        return JsonResponse(response_data, status=200)
        

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([])
def saveprofile(request, user_id):
    try:
        data = json.loads(request.body)
        firstName = data.get('firstName', '')
        lastName = data.get('lastName', '')
        email = data.get('email', '')
        oldpassword = data.get('oldpassword', '')
        newpassword = data.get('newpassword', '')
        
        
        u = User.objects.filter(userid=user_id).first()
        if u:
            if len(oldpassword.strip()) > 0:
                # oldpassword_ = hashlib.md5(oldpassword.encode()).hexdigest()
                if u.check_password(newpassword):
                    u.first_name = firstName
                    u.last_name = lastName
                    u.email = email
                    #u.password = hashlib.md5(newpassword.encode()).hexdigest()
                    u.set_password(newpassword)
                    u.save()
                    update_session_auth_hash(request, u)  
                    response_data = {
                'status': 'success',
                'message': 'Profile data & passoword updated successfully'
            }

                    return JsonResponse(response_data, status=200)
                else:
                    response_data = {
                'error': 'Password is Incorrect',
                'message': 'Password is Incorrect'
            }
                    return  JsonResponse(response_data, status=401)
                    
            else:
                u.first_name = firstName
                u.last_name = lastName
                u.email = email
                u.save()
                response_data = {
                'status': 'success',
                'message': 'Profile data updated successfully'
            }

                return JsonResponse(response_data, status=200)
        else:
            JsonResponse({'error': 'Unauthorized user'}, status=401)
    except Exception as e:
      return JsonResponse({'error': str(e)}, status=500)

def test(request):
     return render(request, 'test.html', {}) 

def index(request):
    # blog = Blog.objects().first()
    # if blog:
    #     blog.delete()
    # new_blog = Blog(title="MongoDB with Django", content="Tutorial content")
    # new_blog.save()
    # blogs = Blog.objects()
    # blogs_data = [{"title": b.title, "content": b.content} for b in blogs]
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