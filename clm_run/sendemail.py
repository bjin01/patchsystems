#!/usr/bin/python3.6

# script to send mail via smarthost
# (do NOT name this script "smtplib.py")

# load requirements
import datetime
import smtplib
import argparse
from email.mime.text import MIMEText
import sys

parser = argparse.ArgumentParser(description='Send an email.')
parser.add_argument('--debuglevel', type=int, default=0, help='Debug level')
parser.add_argument('--server_host', type=str, required=True, help='SMTP server host')
parser.add_argument('--server_port', type=int, default=25, help='SMTP server port')
parser.add_argument('--server_user', type=str, default='anonymous', help='SMTP server user')
parser.add_argument('--server_pass', type=str, default='', help='SMTP server password')
parser.add_argument('--address_from', type=str, required=True, help='From email address')
parser.add_argument('--address_to', type=str, required=True, help='To email address')
parser.add_argument('--mail_subject', type=str, default='test', help='Email subject')
parser.add_argument('--mail_body', type=str, default='This is a test email.', help='Email body')

args = parser.parse_args()

# Create the email message
msg = MIMEText(args.mail_body)
msg['Subject'] = args.mail_subject
msg['From'] = args.address_from
msg['To'] = args.address_to

# Send the email
try:
    with smtplib.SMTP(args.server_host, args.server_port) as server:
        server.set_debuglevel(args.debuglevel)
        if args.server_user != "anonymous":
            server.login(args.server_user, args.server_pass)
        server.sendmail(args.address_from, [args.address_to], msg.as_string())
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
