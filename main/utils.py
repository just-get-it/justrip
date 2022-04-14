from django.core.mail import send_mail
import math
import random
import string
from .models import Charges


def send_email(subject,message,from_email,to_list):
    send_mail(subject,message,from_email,to_list,fail_silently=True)
    return True

# function to generate OTP
def generateOTP6digit() :

    # Declare a string variable
    # which stores all string
    string = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    OTP = ""
    length = len(string)
    for i in range(6) :
        OTP += string[math.floor(random.random() * length)]

    return OTP

def randomStringDigits(stringLength=30):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))

 