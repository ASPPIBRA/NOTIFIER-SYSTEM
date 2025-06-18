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

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("email_sender.log"),
        logging.StreamHandler()
    ]
)

class EmailSender:
    def __init__(
        self,
        config_path: str = "config.json",
        env_path: str = ".env",
        dry_run: bool = False,
        selected_email: Optional[str] = None
    ) -> None:
        # Carrega configurações gerais
        self.config = self._load_config(config_path)
        load_dotenv(env_path)

        # Carrega contas de e-mail do .env
        emails_raw: Optional[str] = os.getenv("EMAILS_JSON")
        if not emails_raw:
            logging.error("Variável EMAILS_JSON não está definida no arquivo .env.")
            raise ValueError("Variável EMAILS_JSON ausente no .env")
        try:
            email_options: Dict[str, str] = json.loads(emails_raw)
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao interpretar EMAILS_JSON como JSON: {e}")
            raise

        # Seleção interativa de conta, caso não seja fornecida como argumento
        if not selected_email:
            print("\n📧 Contas de e-mail disponíveis para envio:")
            for i, email in enumerate(email_options.keys(), start=1):
                print(f"{i}. {email}")
            choice = input("Escolha o número do e-mail a ser utilizado: ").strip()
            try:
                selected_email = list(email_options.keys())[int(choice) - 1]
            except (IndexError, ValueError):
                logging.error("Escolha inválida para o e-mail.")
                raise ValueError("Escolha inválida.")
        elif selected_email not in email_options:
            logging.error(f"O e-mail selecionado '{selected_email}' não está presente nas opções.")
            raise ValueError("E-mail selecionado inválido.")

        # Define credenciais e parâmetros
        self.email_user: str = selected_email
        self.email_password: str = email_options[self.email_user]
        self.smtp_server: str = self.config.get('smtp_server')
        self.smtp_port: int = self.config.get('smtp_port')
        self.subject: str = self.config.get('subject')
        self.template_file: str = self.config.get('template_file')
        self.sleep_time: int = self.config.get('sleep_time', 1)
        self.default_body: str = self.config.get(
            'default_body',
            'Confira nossa oferta exclusiva!'
        )
        self.dry_run: bool = dry_run

        if self.dry_run:
            logging.info("Modo Dry Run ativado - Nenhum e-mail será enviado.")

        
        # Caminho absoluto para templates HTML
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))
        

    def _load_config(self, path: str) -> Dict:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Erro ao carregar configuração: {e}")
            raise

    def validate_email_address(self, email: str) -> bool:
        try:
            validate_email(email)
            return True
        except EmailNotValidError as e:
            logging.warning(f"Email inválido: {email} - {e}")
            return False

    def render_template(self, context: Dict[str, str]) -> str:
        try:
            template = self.env.get_template(self.template_file)
            return template.render(**context)
        except TemplateNotFound as e:
            logging.error(f"Template '{self.template_file}' não encontrado no diretório de templates.")
            raise

    def create_email(
        self,
        recipient: str,
        name: str,
        body_html: str,
        attachments: Optional[List[str]] = None
    ) -> EmailMessage:
        msg = EmailMessage()
        msg['Subject'] = self.subject
        msg['From'] = self.email_user
        msg['To'] = recipient
        msg.set_content(f"Olá {name},\n\n{self.default_body}")
        msg.add_alternative(body_html, subtype='html')

        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    logging.warning(f"Anexo não encontrado: {file_path}")
                    continue
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(file_path)
                    msg.add_attachment(
                        file_data,
                        maintype='application',
                        subtype='octet-stream',
                        filename=file_name
                    )
        return msg

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def send_email(self, msg: EmailMessage) -> None:
        if self.dry_run:
            logging.info(f"[Dry Run] Simulação de envio para: {msg['To']}")
            return

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                logging.info(f"E-mail enviado para {msg['To']}")
        except smtplib.SMTPException as e:
            logging.error(f"Erro SMTP ao enviar e-mail para {msg['To']}: {e}")
            raise

    def send_bulk_emails(
        self,
        contacts: List[Dict[str, str]],
        attachments: Optional[List[str]] = None
    ) -> None:
        success_count = 0
        fail_count = 0

        if attachments:
            valid_attachments = [f for f in attachments if os.path.exists(f)]
            invalid_attachments = [f for f in attachments if not os.path.exists(f)]
            for f in invalid_attachments:
                logging.warning(f"Arquivo de anexo não encontrado e será ignorado: {f}")
            attachments = valid_attachments

        for contact in contacts:
            name: Optional[str] = contact.get('name')
            email: Optional[str] = contact.get('email')
            if not name or not email:
                logging.warning(f"Contato malformado: {contact}")
                fail_count += 1
                continue
            if not self.validate_email_address(email):
                fail_count += 1
                continue

            context = {'name': name}
            try:
                body_html = self.render_template(context)
                msg = self.create_email(email, name, body_html, attachments)
                self.send_email(msg)
                success_count += 1
            except Exception as e:
                logging.error(f"Erro ao processar {email}: {e}", exc_info=True)
                fail_count += 1

            time.sleep(self.sleep_time)

        logging.info(f"\nResumo do envio: {success_count} enviados com sucesso, {fail_count} falharam.")


# 🚀 Ponto de entrada
if __name__ == "__main__":
    try:
        with open('contacts.json', 'r', encoding='utf-8') as f:
            contacts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Erro ao carregar lista de contatos: {e}")
        contacts = []

    try:
        email_sender = EmailSender(dry_run=False)
        email_sender.send_bulk_emails(
            contacts,
            attachments=['attachments/Art.pdf']
        )
    except Exception as e:
        logging.critical(f"Falha ao inicializar o envio de e-mails: {e}", exc_info=True)
