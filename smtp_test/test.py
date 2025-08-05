import smtplib
from email.message import EmailMessage


server = smtplib.SMTP('localhost', 8001)

message = EmailMessage()
message['FROM'] = 'sender@example.com'
message['TO'] = ['receiver@example.com']
message['SUBJECT'] = 'test subject 1'
message.set_content('test content')

server.sendmail(message['FROM'], message['TO'], message.as_string())
server.close()