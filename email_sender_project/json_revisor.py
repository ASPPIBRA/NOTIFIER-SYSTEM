import json
import os
import re
import logging
import shutil
import argparse
from datetime import datetime

try:
    import simplejson as json_parser
except ImportError:
    import json as json_parser

def configurar_logger(log_path=None):
    """Configura logging para console e opcionalmente para arquivo."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (se log_path for fornecido)
    if log_path:
        fh = logging.FileHandler(log_path, encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

def verificar_permissoes(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        logging.error(f"O arquivo '{caminho_arquivo}' não foi encontrado.")
        return False
    if not os.access(caminho_arquivo, os.R_OK):
        logging.error(f"Sem permissão de leitura para o arquivo '{caminho_arquivo}'.")
        return False
    if not os.access(os.path.dirname(caminho_arquivo) or ".", os.W_OK):
        logging.error(f"Sem permissão de escrita no diretório do arquivo '{caminho_arquivo}'.")
        return False
    return True

def fazer_backup(caminho_arquivo):
    nome_arquivo, extensao = os.path.splitext(caminho_arquivo)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_backup = f"{nome_arquivo}_backup_{timestamp}{extensao}"
    try:
        shutil.copy2(caminho_arquivo, caminho_backup)
        logging.info(f"Backup criado com sucesso: {caminho_backup}")
    except Exception as e:
        logging.warning(f"Falha ao criar backup: {e}")

def aplicar_correcoes_json(conteudo_original):
    conteudo_corrigido = conteudo_original
    correcoes_aplicadas = []

    nova_versao = re.sub(r',\s*([}\]])', r'\1', conteudo_corrigido)
    if nova_versao != conteudo_corrigido:
        correcoes_aplicadas.append("Remoção de vírgulas extras.")
        conteudo_corrigido = nova_versao

    nova_versao = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', conteudo_corrigido)
    if nova_versao != conteudo_corrigido:
        correcoes_aplicadas.append("Adição de aspas duplas em chaves.")
        conteudo_corrigido = nova_versao

    nova_versao = re.sub(r"\'([^']*)\'", r'"\1"', conteudo_corrigido)
    if nova_versao != conteudo_corrigido:
        correcoes_aplicadas.append("Substituição de aspas simples por aspas duplas.")
        conteudo_corrigido = nova_versao

    nova_versao = conteudo_corrigido.replace('\n', '\\n').replace('\t', '\\t')
    if nova_versao != conteudo_corrigido:
        correcoes_aplicadas.append("Escape de quebras de linha e tabulações.")
        conteudo_corrigido = nova_versao

    return conteudo_corrigido, correcoes_aplicadas

def revisar_e_corrigir_json(caminho_arquivo):
    logging.info(f"Iniciando revisão do arquivo: {caminho_arquivo}")

    if not verificar_permissoes(caminho_arquivo):
        return False

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo_original = f.read()
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo: {e}")
        return False

    try:
        dados = json_parser.loads(conteudo_original)
        logging.info("O arquivo JSON é sintaticamente válido.")
    except json.JSONDecodeError as e:
        logging.warning(f"Erro de sintaxe JSON: {e}")
        conteudo_corrigido, correcoes_aplicadas = aplicar_correcoes_json(conteudo_original)

        try:
            dados = json_parser.loads(conteudo_corrigido)
            logging.info("JSON corrigido com sucesso.")
            for c in correcoes_aplicadas:
                logging.info(f"Correção aplicada: {c}")
        except json.JSONDecodeError as e2:
            logging.error(f"Erro após tentativa de correção: {e2}")
            return False

        conteudo_original = conteudo_corrigido

    fazer_backup(caminho_arquivo)

    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        logging.info("Arquivo JSON salvo com sucesso.")
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Revisar e corrigir arquivo JSON.")
    parser.add_argument("arquivo", help="Caminho do arquivo JSON a ser revisado")
    parser.add_argument("-l", "--log", help="Caminho para salvar o arquivo de log", default=None)
    args = parser.parse_args()

    configurar_logger(args.log)

    if revisar_e_corrigir_json(args.arquivo):
        logging.info("Processo concluído com sucesso.")
    else:
        logging.error("Processo encerrado com erros.")

if __name__ == "__main__":
    main()
