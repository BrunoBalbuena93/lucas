import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from json import load
from os.path import join


def sendEmail(subject, message):
    port = 465

    # Retrieving creds
    with open(join('records', 'creds.json'), 'r') as f:
        creds = load(f)


    emisor = creds['emiter']
    password = creds['password']
    receptors = creds['recievers']
    
    # Escribiendo el mensaje
    body = message

    # Crear conexion SSL
    context = ssl.create_default_context()

    # Logeando
    with smtplib.SMTP_SSL('smtp.gmail.com', port, context=context) as server:
        server.login(emisor, password)
        msg = MIMEMultipart()
        msg['From'] = emisor
        msg['To'] = ', '.join(receptors)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        [server.sendmail(emisor, receptor, msg.as_string()) for receptor in receptors]

