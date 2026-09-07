#!/usr/bin/env python3
"""Send the newsletter email. Reads SMTP creds from ~/.hermes/.env (SMTP_* or EMAIL_* keys).

Usage: send_email.py --html FILE --text FILE [--subject "..."] [--no-send]
--no-send validates files + prints what WOULD be sent (dry run).
"""
import argparse, os, re, smtplib, ssl, sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

ENV_PATH = os.path.expanduser("~/.hermes/.env")
JOB_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smtp.env")
TO = os.environ.get("MAIL_TO", "YOU@example.com")


def load_env():
    vals = {}
    for p in (ENV_PATH, JOB_ENV_PATH):  # job-local file wins
        if not os.path.exists(p):
            continue
        for ln in open(p):
            ln = ln.strip()
            if ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            vals[k.strip()] = v.strip().strip('"').strip("'")

    def pick(*names):
        for n in names:
            if vals.get(n):
                return vals[n]
        for n in names:
            if os.environ.get(n):
                return os.environ[n]
        return None

    return {
        "host": pick("SMTP_HOST", "EMAIL_SMTP_HOST") or "smtp.gmail.com",
        "port": int(pick("SMTP_PORT", "EMAIL_SMTP_PORT") or "587"),
        "user": pick("SMTP_USER", "EMAIL_ADDRESS"),
        "pw": pick("SMTP_PASS", "EMAIL_PASSWORD"),
        "frm": pick("MAIL_FROM", "SMTP_USER", "EMAIL_ADDRESS"),
    }


def enforce_dark_code_styles(html):
    """Safety net: bare <code>/<pre> render BLACK on dark backgrounds in many mail
    clients. Force the dark-theme code colors regardless of what compose emitted."""
    html = re.sub(r"<code(?![^>]*\bcolor:)", '<code style="color:#7ee787;"', html)
    html = re.sub(r"<pre(?![^>]*\bcolor:)",
                  '<pre style="background:#0d1117;border:1px solid #30363d;'
                  'border-radius:6px;padding:10px 12px;font-size:12px;'
                  'color:#7ee787;overflow-x:auto;"', html)
    # <code> inside a <pre> already inherits #7ee787; a nested color is harmless anyway.
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--subject", default="AI Newsletter")
    ap.add_argument("--to", default=TO)
    ap.add_argument("--from-name", default="Hermes AI Newsletter")
    ap.add_argument("--no-send", action="store_true")
    args = ap.parse_args()

    html = enforce_dark_code_styles(open(args.html, encoding="utf-8").read())
    text = open(args.text, encoding="utf-8").read()
    if len(html) < 500:
        sys.exit("REFUSING: html too short — newsletter looks uncomposed")

    c = load_env()
    if args.no_send:
        print(f"DRY OK: to={args.to} subject={args.subject!r} html={len(html)}B text={len(text)}B "
              f"smtp={c['host']}:{c['port']} user={'set' if c['user'] else 'MISSING'} pw={'set' if c['pw'] else 'MISSING'}")
        return
    if not c["user"] or not c["pw"]:
        sys.exit("MISSING CREDENTIALS: add SMTP_USER/SMTP_PASS (or EMAIL_ADDRESS/EMAIL_PASSWORD) to ~/.hermes/.env")

    msg = EmailMessage()
    msg["Subject"] = args.subject
    msg["From"] = f"{args.from_name} <{c['frm']}>"
    msg["To"] = args.to
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    ctx = ssl.create_default_context()
    if c["port"] == 465:
        with smtplib.SMTP_SSL(c["host"], c["port"], context=ctx, timeout=45) as s:
            s.login(c["user"], c["pw"])
            s.send_message(msg)
    else:
        with smtplib.SMTP(c["host"], c["port"], timeout=45) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.ehlo()
            s.login(c["user"], c["pw"])
            s.send_message(msg)
    print(f"SENT to {TO}: {args.subject}")


if __name__ == "__main__":
    main()
