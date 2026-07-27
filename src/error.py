
import sys
import smtplib


def error(msg):
    _handle(line=f"Error: {msg}")

def internal(msg):
    _handle(line=f"INTERNAL ERROR (this is most certainly a bug): {msg}")

def token(token, msg):
    _handle(line=f"Error on line {token.line}: {msg}")

def _handle(line):
    print(line, file=sys.stderr)
    sys.exit(1)

