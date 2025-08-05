from email.message import EmailMessage

from core.config import settings


class MessageBuilder:
    def __init__(self):
        self.message = EmailMessage()
    
    def set_content(self, content: str):
        self.message.set_content(content)
        return self
    
    def set_sender(self, sender_email: str | None = None):
        if sender_email is None:
            sender_email = settings.smtp_default_sender
        self.message['From'] = sender_email
        return self
    
    def set_recipients(self, recipients: list[str]):
        self.message['To'] = recipients
        return self
    
    def build(self) -> EmailMessage:
        return self.message
