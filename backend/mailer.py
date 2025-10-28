import os
import smtplib
from email.mime.text import MIMEText


def send_email(to_addr: str, subject: str, body: str) -> bool:
    """
    Best-effort email sender. If SMTP env vars are not configured,
    prints the email to console and returns True so that local dev
    can proceed without real delivery.
    Env vars:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_USE_TLS
    """
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "0") or 0)
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("SMTP_FROM", user or "noreply@example.com")
    # SSL for port 465; TLS (STARTTLS) usually for 587
    use_ssl = os.getenv("SMTP_USE_SSL", "").lower() in ("1", "true", "yes") or port == 465
    use_tls = (os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")) and not use_ssl

    if not host or not port or not from_addr:
        print("[MAIL DEV] To:", to_addr)
        print("[MAIL DEV] Subject:", subject)
        print("[MAIL DEV] Body:\n", body)
        # Also write to a local dev log for easy retrieval
        try:
            log_path = os.getenv("OTP_LOG") or os.path.join(os.path.dirname(__file__), "otp_dev.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"To: {to_addr}\nSubject: {subject}\n{body}\n{'-'*40}\n")
        except Exception as e:
            print("[MAIL DEV] Failed to write OTP log:", e)
        return True

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=10) as server:
                if user and pwd:
                    server.login(user, pwd)
                server.sendmail(from_addr, [to_addr], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                if use_tls:
                    server.starttls()
                if user and pwd:
                    server.login(user, pwd)
                server.sendmail(from_addr, [to_addr], msg.as_string())
        return True
    except Exception as e:
        print("[MAIL ERROR]", e)
        # Still surface the content for visibility in dev
        print("[MAIL FALLBACK] To:", to_addr)
        print("[MAIL FALLBACK] Subject:", subject)
        print("[MAIL FALLBACK] Body:\n", body)
        return False
