from django.core.cache import cache
from django.core.mail import send_mail 
from django.core.mail import BadHeaderError
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from smtplib import SMTPException
from .models import UserProfile
import random



def generate_verification_code():
    return str(random.randint(100000, 999999)) 

def store_verification_code(user, code):
    cache.set(f"email_verification_{user.id}", code, timeout=300)

def send_verification_email(user, code):
    subject = "کد تأیید ایمیل"
    message = f"کد تأیید ایمیل شما: {code}"
    from_email = 'mostafaabdi.job@gmail.com'
    recipient_list = [user.email]
    try:
        send_mail(subject, message, from_email, recipient_list)
    except BadHeaderError:
        print("Invalid header found.")
    except SMTPException as e:
        print(f"SMTP error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


class UserSignUp(APIView):
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="ایجاد کاربر جدید",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='نام کاربری'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='رمز عبور'),
                'password2': openapi.Schema(type=openapi.TYPE_STRING, description='تکرار رمز عبور'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='ایمیل'),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='شماره تلفن (اختیاری)', default=""),
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='آدرس (اختیاری)', default=""),
            },
            required=['username', 'password', 'password2', 'email']
        ),
        responses={
            201: openapi.Response(description="کاربر با موفقیت ایجاد شد"),
            400: openapi.Response(description="خطای درخواست"),
            409: openapi.Response(description="نام کاربری قبلاً ثبت شده است"),
        }
    )
    def post(self, request):

        try:
            username = request.data['username']
            password = request.data['password']
            email = request.data['email']
            password2 = request.data['password2']

            if password != password2:
                return Response({"رمز عبور با رمز عبور اول مقایرت ندارد!":""}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(username=username).exists():
                return  Response({"error":"این نام کاربری قبلا ثبت شده!"},status=status.HTTP_409_CONFLICT)

            if not email.endswith('@gmail.com'):
                return Response({"error": "ایمیل باید از دامنه @gmail.com باشد!"}, status=status.HTTP_400_BAD_REQUEST)

        except KeyError:
            return Response({"error":"اطلاعات خواسته شده را وارد کنید"},status=status.HTTP_400_BAD_REQUEST)

        address = request.data.get('address', '')
        phone = request.data.get('phone', '')

        user = User.objects.create_user(username=username, password=password, email=email,)
        
        code = generate_verification_code()

        store_verification_code(user, code)

        send_verification_email(user, code)

        if address:
            userprofile = UserProfile.objects.get(user=user)
            userprofile.address = address 
            userprofile.save()
        
        if phone:  
            userprofile = UserProfile.objects.get(user=user)
            userprofile.phone = phone
            number_phone = len(phone)
            if number_phone <= 11 and phone[0] == '0' and phone[1] == '9' :
                userprofile.save()
            else:
                return Response({"message":" شما با موفقیت ثبت نام شدید.شماره تلفن اشتباه است!"}, status=status.HTTP_201_CREATED)


        return Response({"message":"شما با موفقیت ثبت نام شدید"}, status=status.HTTP_201_CREATED)


class EmailConfirmation(APIView):
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="ایجاد کاربر جدید",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='کد تایید'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='نام کاربری'),
            },
            required=['code','username']
        ),
        responses={
            200: openapi.Response(description="ایمیل تایید شد"),
            400: openapi.Response(description="خطای درخواست"),
            
        }
    )

    def post(self, request):
        username = request.data.get('username')
        code = request.data.get('code')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "کاربر یافت نشد!"}, status=status.HTTP_404_NOT_FOUND)

        cached_code = cache.get(f"email_verification_{user.id}") 
        userprofile = UserProfile.objects.get(user=user)
        if cached_code == code:
            userprofile.email_confirmation = True
            userprofile.save()
            cache.delete(f"email_verification_{user.id}")  # حذف کد از Redis
            return Response({"message": "ایمیل شما با موفقیت تأیید شد."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "کد تأیید نامعتبر است یا منقضی شده است."}, status=status.HTTP_400_BAD_REQUEST)


class EditProfile(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_description="ویرایش پروفایل کاربری",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='آدرس (اختیاری)'),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='شماره تلفن (اختیاری)'),
            },
            required=[]
        ),
        responses={
            200: openapi.Response(description="ویرایش پروفایل با موفقیت انجام شد"),
            400: openapi.Response(description="خطای درخواست"),
            401: openapi.Response(description="شما باید وارد شده باشید"),
            404: openapi.Response(description="کاربر یافت نشد"),
        }
        )
    def put(self,request):
        
        try:
            user = request.user
            userprofile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return Response({"error": "پروفایل یافت نشد!"}, status=status.HTTP_404_NOT_FOUND)
        except KeyError:
            return Response({"error":"اطلاعات خواسته شده را وارد کنید"},status=status.HTTP_400_BAD_REQUEST)
        
        address = request.data.get('address', userprofile.address)
        
        phone = request.data.get('phone', userprofile.phone)
        number_phone = len(phone)

        if address:
            userprofile.address = address
            userprofile.save()
        
        if number_phone == 11 and phone[0] == '0' and phone[1] == '9' :
            userprofile.phone = phone
            userprofile.save()

        
        else : 
            return Response({"error": "شماره تلفن اشتباه است!"}, status=status.HTTP_400_BAD_REQUEST)


        return Response({"message":"پروفایل شما با موفقیت ویرایش شد."}, status=status.HTTP_200_OK)  

