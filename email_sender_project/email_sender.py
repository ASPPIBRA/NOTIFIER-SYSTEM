import smtplib
import ssl
import json
import time
import os
from typing import List, Dict, Optional
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from tenacity import retry, stop_after_attempt, wait_fixed
from dotenv import load_dotenv
import logging
from email_validator import validate_email, EmailNotValidError

# Configuração do logging para arquivo e console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("email_sender.log"),
        logging.StreamHandler()
    ]
)

class EmailSender:
    def __init__(self, config_path: str = "config.json", env_path: str = ".env", dry_run: bool = False) -> None:
        """
        Inicializa o EmailSender com configurações e variáveis de ambiente.
        """
        self.config = self._load_config(config_path)
        load_dotenv(env_path)

        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.smtp_server = self.config.get('smtp_server')
        self.smtp_port = self.config.get('smtp_port')
        self.subject = self.config.get('subject')
        self.template_file = self.config.get('template_file')
        self.sleep_time = self.config.get('sleep_time', 1)
        self.default_body = self.config.get('default_body', 'Confira nossa oferta exclusiva!')
        self.dry_run = dry_run

        self.env = Environment(loader=FileSystemLoader('./templates'))

    def _load_config(self, path: str) -> Dict:
        """Carrega as configurações do arquivo JSON com tratamento de erro."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Erro ao carregar configuração: {e}")
            raise

    def validate_email_address(self, email: str) -> bool:
        """Valida um endereço de e-mail."""
        try:
            validate_email(email)
            return True
        except EmailNotValidError as e:
            logging.warning(f"Email inválido: {email} - {str(e)}")
            return False

    def render_template(self, context: Dict) -> str:
        """Renderiza o template Jinja2 com o contexto fornecido."""
        try:
            template = self.env.get_template(os.path.basename(self.template_file))
            return template.render(**context)
        except TemplateNotFound as e:
            logging.error(f"Template não encontrado: {e}")
            raise

    def create_email(self, recipient: str, name: str, body_html: str, attachments: Optional[List[str]] = None) -> EmailMessage:
        """Cria o objeto de mensagem de e-mail."""
        msg = EmailMessage()
        msg['Subject'] = self.subject
        msg['From'] = self.email_user
        msg['To'] = recipient
        msg.set_content(f"Olá {name},\n\n{self.default_body}")
        msg.add_alternative(body_html, subtype='html')

        if attachments:
            for file_path in attachments:
                try:
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        file_name = os.path.basename(file_path)
                        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
                except FileNotFoundError:
                    logging.warning(f"Anexo não encontrado: {file_path}")
        return msg

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def send_email(self, msg: EmailMessage) -> None:
        """Envia um e-mail com retry automático."""
        if self.dry_run:
            logging.info(f"[Dry Run] Simulação de envio para: {msg['To']}")
            return

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            logging.info(f"E-mail enviado para {msg['To']}")

    def send_bulk_emails(self, contacts: List[Dict[str, str]], attachments: Optional[List[str]] = None) -> None:
        """Envia e-mails em massa para uma lista de contatos."""
        for contact in contacts:
            name = contact.get('name')
            email = contact.get('email')

            if not name or not email:
                logging.warning(f"Contato malformado: {contact}")
                continue

            if not self.validate_email_address(email):
                continue

            context = {'name': name}
            try:
                body_html = self.render_template(context)
                msg = self.create_email(email, name, body_html, attachments)
                self.send_email(msg)
            except Exception as e:
                logging.error(f"Erro ao processar {email}: {e}")
            time.sleep(self.sleep_time)

# Execução direta
if __name__ == "__main__":
    contacts = [
        {'name': 'ASPPIBRA-DAO', 'email': 'associaasppibra@gmail.com'},
        {'name': 'GP', 'email': 'gp.samarinat@gmail.com'},
        {'name': 'Contato inválido'}
    ]

    email_sender = EmailSender(dry_run=False)
    email_sender.send_bulk_emails(contacts, attachments=['attachments/Art.pdf'])
