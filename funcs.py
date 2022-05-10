import random
from smtplib import *

#function for generating random otp
def generate_otp():
    otp=""
    for i in range(0,4):
        random_num=str(random.randint(0,9))
        otp+=random_num
    return otp

#function for sending the otp to the users
def send_otp(reciever,msg):
    my_mail = "pradyublog@gmail.com"
    my_password = "sivajivaailajelabi"
    # creating a smtp obj (establishing the connection)
    connection = SMTP("smtp.gmail.com", 587)
    # securing the connection
    connection.starttls()
    # logging into our mail
    connection.login(user=my_mail, password=my_password)
    # sending the mail
    connection.sendmail(from_addr=my_mail, to_addrs=reciever, msg=f"Your OTP for Pradyu's Blog is {msg} Do not share it with anyone")
    # closing the conection ie obj file
    connection.close()
