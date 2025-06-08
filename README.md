# NOTIFIER-SYSTEM

# 📬 Sistema Automatizado de Envio de E-mails com Anexos

Este projeto é um sistema completo e modular de envio automatizado de e-mails personalizados em massa, com suporte a anexos, templates HTML, validação de e-mails e registro de logs. Ideal para campanhas, notificações institucionais e comunicação em escala.

---

## ✅ Funcionalidades Atuais

### 🔐 Autenticação e Conexão Segura

- Autenticação via `.env` com `EMAIL_USER` e `EMAIL_PASSWORD`
- Conexão segura via `SMTP_SSL` com verificação de servidor SMTP e porta

### 🧩 Arquitetura Modular

- Classe `EmailSender` centraliza a lógica de envio
- Separação clara de funções: renderização de template, criação da mensagem, envio e leitura de configurações

### 📨 Envio de E-mails Personalizados

- Uso de **templates HTML com Jinja2** para personalização de conteúdo
- Suporte a e-mail alternativo em texto plano para compatibilidade

### 📎 Anexos

- Suporte a envio de múltiplos arquivos
- Validação de caminho de arquivo com `FileNotFoundError` tratado por log

### 🧪 Modo de Teste (Dry Run)

- Flag `dry_run=True` permite simular os envios sem enviar de fato, ideal para testes

### 🔄 Repetição Automática em Caso de Erros Temporários

- Com `tenacity`, o sistema tenta reenviar até 3 vezes com intervalo fixo em caso de falhas

### 📜 Validação de E-mails

- Validação sintática e semântica usando a biblioteca `email_validator`

### 🧠 Logs e Monitoramento

- Registro detalhado de operações com `logging`, incluindo:
  - Envio bem-sucedido
  - E-mails inválidos
  - Falhas de conexão
  - Anexos ausentes
  - Contatos malformados

---

## ⚙️ Estrutura do Projeto

```bash
notifier_system/
├── email_sender_project/
│   ├── templates/
│   │   └── template.html
│   ├── attachments/
│   │   └── Art.pdf
│   ├── email_sender.py
│   ├── config.json
│   ├── .env
│   └── email_sender.log

## 📁 Exemplo de `config.json`

```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 465,
  "subject": "Informativo ASPPIBRA-DAO",
  "template_file": "template.html",
  "sleep_time": 2,
  "default_body": "Confira nossa oferta exclusiva!"
}


##📋 Exemplo de .env
EMAIL_USER=seuemail@gmail.com
EMAIL_PASSWORD=suasenhaouappkey


##🧪 Execução

python email_sender.py


## 🛠️ Sugestões de Melhoria – Versão 2.0

### 📌 Funcionalidades Planejadas

| Nº  | Funcionalidade                                         | Descrição |
|-----|---------------------------------------------------------|-----------|
| 1   | 📎 Anexos dinâmicos por destinatário                    | Permitir anexar arquivos personalizados por contato. |
| 2   | 🧠 Contexto dinâmico por destinatário                   | Permitir variáveis exclusivas em cada e-mail, como nome da loja, desconto etc. |
| 3   | 📥 Leitura de contatos de planilha (.xlsx)              | Importar diretamente de arquivos Excel para facilitar integração com sistemas externos. |
| 4   | 📝 Templates em Markdown                                | Escrever templates em Markdown e converter automaticamente para HTML. |
| 5   | 🔁 Logs com rotação automática                          | Substituir logs contínuos por logs diários com backup e limpeza. |
| 6   | 📊 Geração de relatórios automáticos                    | Criar JSON ou CSV com status do envio (sucesso/falha por contato). |
| 7   | 🧪 Teste de conexão SMTP                                | Validar login e conexão SMTP antes de iniciar o envio em massa. |
| 8   | 🔧 Interface CLI (linha de comando)                     | Executar a ferramenta com argumentos via terminal (como `--template`, `--dry-run`). |
| 9   | 🌐 Interface Web com Flask                              | Criar painel visual para não programadores enviarem e-mails com mais facilidade. |
| 10  | 🤖 Integrações externas (API, Telegram, Google Sheets)  | Conectar o sistema a CRMs, Google Sheets e notificações automatizadas por bot. |

---

## 👨‍💻 Contribuição

Sinta-se à vontade para sugerir melhorias ou abrir pull requests com novas funções.  
Para dúvidas técnicas ou operacionais, entre em contato com a equipe da **ASPPIBRA-DAO**.

---

## 📄 Licença

Este projeto está licenciado sob os termos da **MIT License**.  
Consulte o arquivo `LICENSE` para mais detalhes.
