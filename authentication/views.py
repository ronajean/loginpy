from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from loginpy import settings
from django.core.mail import EmailMessage, send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from . tokens import generate_token

# Create your views here.
def home(request):
    return render(request,"authentication/index.html")

def signup(request):

    if request.method == "POST":
       # username = request.POST.get('username')
        username = request.POST['username'] #takes the username field
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        #validation. email must not be repeated
        if User.objects.filter(username=username):
            messages.error(request, "Username already exists!")
            return redirect('home')
        
        if User.objects.filter(email=email):
            messages.error(request, "Email already registered!")
            return redirect('home')
        
        #validation; length of username
        if len(username) > 10:
            messages.error(request, "Username must be under 10 characters")
        
        #validation: password matches
        if pass1 != pass2:
            messages.error(request, "Passwords didn't match!")
        
        #valdiation: username must be alphanumeric only
        if not username.isalnum():
            messages.error(request, "Username must be alphanumeric")
            return redirect('home')

        #register the user to the database
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False #user is not automatically activated 

        #save
        myuser.save()

        #show a message that the user has registered successfully
        messages.success(request, "Your account has been successfully created! We have sent you a confirmation email. Please confirm your email in order to activate your account")

        #sending welcome email (iba pa sa confimation email) 
        subject = "Welcome to our app django login!"
        message = "Hello, " + myuser.first_name + "!! \n" + "Welcome to this!! \n Thank you for visiting \n We sent you a confirmation email"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)

        #confirmation email
        current_site = get_current_site(request)
        email_subject = "Confirm your email - Django Login"
        message2 = render_to_string('email_confirmation.html',{
            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser)
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email]
        )
        email.fail_silently = True
        email.send()  #send the email


        #once registered, user must be redirected to sign in page
        return redirect('signin')
 
    return render(request, "authentication/signup.html")

def signin(request):

    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']

        #authenticate user
        #
        user = authenticate(request=request, username=username, password=pass1) #returns None or not None response
        #None - user is not authenticated

        if user is not None:
            login(request, user) #authenticated user can login
            fname = user.first_name
            return render(request, "authentication/index.html", {'fname':fname})
        
        else:
            messages.error(request, "Bad credentials!")
            return redirect('home') #not authenticated user redirected to home

    return render(request, "authentication/signin.html")

def signout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('home')

def activate(request, uid64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uid64))
        myuser = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None
    
    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        return redirect('home')
    else: 
        return render(request, 'activation_failes.html')