import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, parsedate_to_datetime
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

logger = logging.getLogger("email_service")

class EmailService:
    @staticmethod
    def test_connection(settings: Dict[str, Any]) -> Dict[str, Any]:
        """Tests both IMAP and SMTP connections using provided credentials."""
        results = {
            "imap": {"success": False, "message": ""},
            "smtp": {"success": False, "message": ""}
        }

        # 1. Test IMAP
        imap_host = (settings.get("imap_host") or "").strip()
        imap_port = int(settings.get("imap_port") or 993)
        imap_user = (settings.get("imap_username") or "").strip()
        imap_pass = (settings.get("imap_password") or "").strip()
        imap_ssl = bool(settings.get("imap_use_ssl", True))

        if imap_host and imap_user and imap_pass:
            try:
                if imap_ssl or imap_port == 993:
                    mail = imaplib.IMAP4_SSL(imap_host, imap_port)
                else:
                    mail = imaplib.IMAP4(imap_host, imap_port)
                mail.login(imap_user, imap_pass)
                mail.select("INBOX")
                mail.logout()
                results["imap"]["success"] = True
                results["imap"]["message"] = f"IMAP connected and authenticated with {imap_host}:{imap_port}"
            except Exception as e:
                err_msg = str(e)
                if "Application-specific password required" in err_msg or "Invalid credentials" in err_msg:
                    err_msg += " (Tip: If using Gmail, use a 16-character Google App Password from myaccount.google.com/apppasswords)"
                results["imap"]["message"] = f"IMAP failed: {err_msg}"
        else:
            results["imap"]["message"] = "IMAP credentials not fully provided"

        # 2. Test SMTP
        smtp_host = (settings.get("smtp_host") or "").strip()
        smtp_port = int(settings.get("smtp_port") or 587)
        smtp_user = (settings.get("smtp_username") or "").strip()
        smtp_pass = (settings.get("smtp_password") or "").strip()
        smtp_tls = bool(settings.get("smtp_use_tls", True))
        smtp_ssl = bool(settings.get("smtp_use_ssl", False))

        if smtp_host and smtp_user and smtp_pass:
            try:
                if smtp_ssl or smtp_port == 465:
                    server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
                else:
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                    if smtp_tls:
                        server.starttls()
                server.login(smtp_user, smtp_pass)
                server.quit()
                results["smtp"]["success"] = True
                results["smtp"]["message"] = f"SMTP connected and authenticated with {smtp_host}:{smtp_port}"
            except Exception as e:
                err_msg = str(e)
                if "Application-specific password required" in err_msg or "535" in err_msg:
                    err_msg += " (Tip: If using Gmail, use a 16-character Google App Password)"
                results["smtp"]["message"] = f"SMTP failed: {err_msg}"
        else:
            results["smtp"]["message"] = "SMTP credentials not fully provided"

        overall = results["imap"]["success"] and results["smtp"]["success"]
        return {
            "success": overall,
            "imap": results["imap"],
            "smtp": results["smtp"]
        }

    @staticmethod
    def send_email(settings: Dict[str, Any], to_email: str, subject: str, body: str, reply_to_msg_id: Optional[str] = None) -> Dict[str, Any]:
        """Sends an email via the user's configured SMTP."""
        smtp_host = (settings.get("smtp_host") or "").strip()
        smtp_port = int(settings.get("smtp_port") or 587)
        smtp_user = (settings.get("smtp_username") or "").strip()
        smtp_pass = (settings.get("smtp_password") or "").strip()
        from_name = (settings.get("from_name") or "RevOps Outbound Agent").strip()
        from_email = (settings.get("from_email") or smtp_user).strip()
        smtp_tls = bool(settings.get("smtp_use_tls", True))
        smtp_ssl = bool(settings.get("smtp_use_ssl", False))

        if not (smtp_host and smtp_user and smtp_pass):
            raise ValueError("SMTP credentials are not configured. Please set them in Settings.")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid(domain=from_email.split("@")[-1] if "@" in from_email else "outbound.ai")

        if reply_to_msg_id:
            msg["In-Reply-To"] = reply_to_msg_id
            msg["References"] = reply_to_msg_id

        # Plain text
        part_text = MIMEText(body, "plain", "utf-8")
        msg.attach(part_text)

        # HTML formatted
        html_formatted = body.replace("\n", "<br/>")
        html_body = f"""<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #1e293b;">
  {html_formatted}
</body>
</html>"""
        part_html = MIMEText(html_body, "html", "utf-8")
        msg.attach(part_html)

        if smtp_ssl or smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            if smtp_tls:
                server.starttls()

        server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()

        return {
            "sent": True,
            "to_email": to_email,
            "from_email": from_email,
            "subject": subject,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def fetch_inbox_emails(settings: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        """Fetches the latest incoming emails from the user's IMAP server."""
        imap_host = (settings.get("imap_host") or "").strip()
        imap_port = int(settings.get("imap_port") or 993)
        imap_user = (settings.get("imap_username") or "").strip()
        imap_pass = (settings.get("imap_password") or "").strip()
        imap_ssl = bool(settings.get("imap_use_ssl", True))

        if not (imap_host and imap_user and imap_pass):
            return []

        if imap_ssl or imap_port == 993:
            mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        else:
            mail = imaplib.IMAP4(imap_host, imap_port)

        mail.login(imap_user, imap_pass)
        mail.select("INBOX")

        status, data = mail.search(None, "ALL")
        if status != "OK" or not data or not data[0]:
            mail.logout()
            return []

        msg_ids = data[0].split()
        target_ids = msg_ids[-limit:]
        target_ids.reverse()

        emails_list = []
        for mid in target_ids:
            try:
                res, msg_data = mail.fetch(mid, "(RFC822)")
                if res != "OK":
                    continue
                raw_bytes = msg_data[0][1]
                msg = email.message_from_bytes(raw_bytes)

                # Subject
                raw_subj = msg.get("Subject", "No Subject")
                decoded_parts = decode_header(raw_subj)
                subj_parts = []
                for content, encoding in decoded_parts:
                    if isinstance(content, bytes):
                        subj_parts.append(content.decode(encoding or "utf-8", errors="replace"))
                    else:
                        subj_parts.append(str(content))
                subject = "".join(subj_parts)

                # From
                from_header = msg.get("From", "Unknown")
                from_name, from_email_addr = parseaddr(from_header)
                if not from_name:
                    from_name = from_email_addr.split("@")[0] if "@" in from_email_addr else from_header

                # Date
                date_str = msg.get("Date")
                received_at = datetime.now(timezone.utc).isoformat()
                if date_str:
                    try:
                        parsed = parsedate_to_datetime(date_str)
                        received_at = parsed.isoformat()
                    except Exception:
                        pass

                # Body extraction
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        cdisp = str(part.get("Content-Disposition"))
                        if ctype == "text/plain" and "attachment" not in cdisp:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                                break
                        elif ctype == "text/html" and not body and "attachment" not in cdisp:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

                body = (body or "").strip()
                if len(body) > 3000:
                    body = body[:3000] + "\n...[truncated]"

                msg_id = msg.get("Message-ID") or f"imap-{mid.decode()}"

                emails_list.append({
                    "message_id": msg_id,
                    "from_name": from_name,
                    "from_email": from_email_addr,
                    "subject": subject,
                    "body": body or "[No text body available]",
                    "received_at": received_at
                })
            except Exception as e:
                logger.warning(f"Failed to parse IMAP message {mid}: {e}")

        mail.logout()
        return emails_list
