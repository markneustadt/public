#!/usr/bin/env python3
"""Send a multipart (text + HTML) newsletter via SMTP.

Credentials via env ONLY (never argv, never a file):
  SMTP_HOST, SMTP_PORT (465 or 587), SMTP_USER, SMTP_PASS, MAIL_FROM
Usage:
  SMTP_HOST=smtp.gmail.com SMTP_PORT=587 SMTP_USER=me@gmail.com \
  SMTP_PASS=xxxx MAIL_FROM=me@gmail.com \
  python3 send_newsletter.py --to YOU@example.com --subject "..." --html-file ...
"""
import argparse, os, smtplib, ssl, sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--to', required=True)
    ap.add_argument('--subject', default='Newsletter')
    ap.add_argument('--html-file', required=True)
    ap.add_argument('--text-file', help='optional plain-text alternative')
    args = ap.parse_args()

    host = os.environ['SMTP_HOST']
    port = int(os.environ.get('SMTP_PORT', '587'))
    user = os.environ['SMTP_USER']
    password = os.environ['SMTP_PASS']
    mail_from = os.environ.get('MAIL_FROM', user)

    html_body = open(args.html_file, encoding='utf-8').read()
    if args.text_file:
        text_body = open(args.text_file, encoding='utf-8').read()
    else:
        # crude text fallback: strip tags
        import re
        text_body = re.sub(r'<[^>]+>', ' ', html_body)
        text_body = re.sub(r'\s+', ' ', text_body).strip()

    msg = EmailMessage()
    msg['Subject'] = args.subject
    msg['From'] = mail_from
    msg['To'] = args.to
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid()
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    if port == 465:
        server = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=30)
    else:
        server = smtplib.SMTP(host, port, timeout=30)
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
    with server:
        server.login(user, password)
        server.send_message(msg)
    print(f'SENT -> {args.to} via {host}:{port} (from {mail_from})')


if __name__ == '__main__':
    sys.exit(main())
