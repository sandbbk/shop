from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import jwt
from megashop.stf import (JWT_ALGORITHM, JWT_EXP_DELTA_SECONDS, JWT_SECRET)
from datetime import datetime, timedelta


def send_email(to_email, subject, template, context):
    from_email = 'support@GoShop.edu'
    html_content = render_to_string(template, {'context': context})
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


