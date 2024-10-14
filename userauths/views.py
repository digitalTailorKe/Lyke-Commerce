from django.http import HttpResponse
from django.shortcuts import redirect, render
import requests
from userauths.forms import UserRegisterForm, ProfileForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.conf import settings
from userauths.models import Profile, User
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import google.auth.transport.requests 
from django.core.files.base import ContentFile

from environs import Env 
env=Env()
env.read_env()

# User = settings.AUTH_USER_MODEL

def register_view(request):
    
    if request.method == "POST":
        form = UserRegisterForm(request.POST or None)
        if form.is_valid():
            new_user = form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, f"Hey {username}, You account was created successfully.")
            new_user = authenticate(username=form.cleaned_data['email'],
                                    password=form.cleaned_data['password1']
            )
            login(request, new_user)
            return redirect("core:index")
    else:
        form = UserRegisterForm()


    context = {
        'form': form,
    }
    return render(request, "userauths/sign-up.html", context)

@csrf_exempt
def auth_receiver(request):
    """
    Google calls this URL after the user has signed in with their Google account.
    This view handles user data received from Google and updates the user in the database.
    """
    token = request.POST.get('credential')
    
    try:
        user_data = id_token.verify_oauth2_token(
            token, google_requests.Request(), env('GOOGLE_OAUTH_CLIENT_ID')
        )

        print(user_data)
        
        # Extract relevant data from the token
        email = user_data.get('email')
        name = user_data.get('name')
        given_name = user_data.get('given_name')
        family_name = user_data.get('family_name')
        picture = user_data.get('picture')
        print(picture)

        # Check if a user with this email already exists
        try:
            print("Auth attempt")
            user, created = User.objects.get_or_create(email=email)
            # Update user details
            user.username = name or user.username
            print("Auth attempt 2")
            if created:
               user.save()
               profile = Profile.objects.create(user=user)
            else:
                profile = user.profile
            print("Auth attempt 3")
            picture_url = picture
            if picture_url:
                image_response = requests.get(picture_url)
                print("Auth attempt 3 pic")
                if image_response.status_code == 200:
                    image_name = f"{user.username}_google_profile.jpg"
                    profile.image.save(image_name, ContentFile(image_response.content))
                    profile.save() 


           # Check if the Profile exists for this user
            # profile, created = Profile.objects.get_or_create(user=user)
            profile.full_name = f"{given_name} {family_name}" or profile.full_name
            profile.verified = True
            # profile.save()
            # Update Profile
            # if not created:
            #     profile.full_name = f"{given_name} {family_name}" or profile.full_name
            #     profile.image = picture or profile.image
            #     profile.save()
        except ValueError:
        # Invalid token
           return HttpResponse(status=403)
        # except User.DoesNotExist:
        #     # Create new user
        #     user = User.objects.create(
        #         email=email,
        #         username=name
        #     )
        #     user.save()

            # Create and update profile

        # Authenticate and log in the user
        login(request, user)
        messages.success(request, f"Welcome {user.username}, you are now logged in.")

        return redirect('core:index')

    except ValueError:
        # Invalid token
        return HttpResponse(status=403)

def login_view(request):
    if request.user.is_authenticated:
        messages.warning(request, f"Hey you are already Logged In.")
        return redirect("core:index")
    
    if request.method == "POST":
        email = request.POST.get("email") # peanuts@gmail.com
        password = request.POST.get("password") # getmepeanuts

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, "You are logged in.")
                return redirect("core:index")
            else:
                messages.warning(request, "User Does Not Exist, create an account.")
    
        except:
            messages.warning(request, f"User with {email} does not exist")
        

    
    return render(request, "userauths/sign-in.html")

        

def logout_view(request):

    logout(request)
    messages.success(request, "You logged out.")
    return redirect("userauths:sign-in")


def profile_update(request):
    profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            new_form.save()
            messages.success(request, "Profile Updated Successfully.")
            return redirect("core:dashboard")
    else:
        form = ProfileForm(instance=profile)

    context = {
        "form": form,
        "profile": profile,
    }

    return render(request, "userauths/profile-edit.html", context)
