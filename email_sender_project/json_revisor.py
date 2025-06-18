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
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')

    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

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

def contar_abrir_fechar(texto):
    return texto.count('{'), texto.count('}'), texto.count('['), texto.count(']')

def aplicar_correcoes_json(conteudo_original):
    conteudo_corrigido = conteudo_original
    correcoes_aplicadas = []

    for invalido in [r'\bNaN\b', r'\bundefined\b', r'\bInfinity\b', r'\b-Infinity\b']:
        nova_versao = re.sub(invalido, 'null', conteudo_corrigido)
        if nova_versao != conteudo_corrigido:
            correcoes_aplicadas.append(f"Substituição de valor inválido: {invalido} → null")
            conteudo_corrigido = nova_versao

    nova_versao = re.sub(r',\s*([}\]])', r'\1', conteudo_corrigido)
    if nova_versao != conteudo_corrigido:
        correcoes_aplicadas.append("Remoção de vírgulas extras antes de fechamento.")
        conteudo_corrigido = nova_versao

    nova_versao = re.sub(r',\s*,+', ',', conteudo_corrigido)
    if nova_versao != conteudo_corrigido:
        correcoes_aplicadas.append("Remoção de vírgulas duplicadas.")
        conteudo_corrigido = nova_versao

    nova_versao = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', conteudo_corrigido)
    if nova_versao != conteudo_corrigido:
        correcoes_aplicadas.append("Adição de aspas em chaves não entre aspas.")
        conteudo_corrigido = nova_versao

    nova_versao = re.sub(r"\'([^']*)\'", r'"\1"', conteudo_corrigido)
    if nova_versao != conteudo_corrigido:
        correcoes_aplicadas.append("Substituição de aspas simples por duplas.")
        conteudo_corrigido = nova_versao

    nova_versao = conteudo_corrigido.replace('\n', '\\n').replace('\t', '\\t')
    if nova_versao != conteudo_corrigido:
        correcoes_aplicadas.append("Escape de quebras de linha e tabulações.")
        conteudo_corrigido = nova_versao

    a1, f1, a2, f2 = contar_abrir_fechar(conteudo_corrigido)
    if a1 > f1:
        conteudo_corrigido += '}' * (a1 - f1)
        correcoes_aplicadas.append(f"Fechamento automático de {a1 - f1} chaves.")
    if a2 > f2:
        conteudo_corrigido += ']' * (a2 - f2)
        correcoes_aplicadas.append(f"Fechamento automático de {a2 - f2} colchetes.")

    return conteudo_corrigido, correcoes_aplicadas

def perguntar_confirmacao(mensagens):
    print("\nCorreções sugeridas:")
    for m in mensagens:
        print(f" - {m}")
    while True:
        resposta = input("\nDeseja aplicar essas correções e salvar o arquivo? (s/n): ").strip().lower()
        if resposta in ('s', 'n'):
            return resposta == 's'
        print("Por favor, responda com 's' ou 'n'.")

def revisar_e_corrigir_json(caminho_arquivo, aplicar_corrigir):
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
        # Mesmo válido, pergunta se quer continuar?
        if aplicar_corrigir:
            print("\nO arquivo JSON é válido. Deseja sobrescrevê-lo com formatação padrão? (s/n): ")
            if not perguntar_confirmacao(["Reformatação do JSON válido"]):
                logging.error("Processo cancelado pelo usuário.")
                return False
            else:
                fazer_backup(caminho_arquivo)
                with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                    json.dump(dados, f, indent=2, ensure_ascii=False)
                logging.info("Arquivo JSON salvo com sucesso com nova formatação.")
                return True
        return True
    except json.JSONDecodeError as e:
        logging.warning(f"Erro de sintaxe JSON: {e}")
        conteudo_corrigido, correcoes_aplicadas = aplicar_correcoes_json(conteudo_original)

        if not correcoes_aplicadas:
            logging.error("Nenhuma correção foi sugerida, mas o JSON é inválido.")
            return False

        logging.info("Correções sugeridas:")
        for c in correcoes_aplicadas:
            logging.info(f" - {c}")

        if not perguntar_confirmacao(correcoes_aplicadas):
            logging.error("Processo cancelado pelo usuário.")
            return False

        try:
            dados = json_parser.loads(conteudo_corrigido)
            logging.info("JSON corrigido com sucesso.")
        except json.JSONDecodeError as e2:
            logging.error(f"Erro após tentativa de correção: {e2}")
            return False

        # Inserir campo "versao" no dicionário raiz, se for dict
        if isinstance(dados, dict):
            dados["versao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            logging.warning("Arquivo JSON não é um objeto/dicionário no topo, não foi possível adicionar campo 'versao'.")

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
    parser.add_argument("--corrigir", action="store_true", help="Aplicar correções após confirmação")
    args = parser.parse_args()

    configurar_logger(args.log)

    if revisar_e_corrigir_json(args.arquivo, args.corrigir):
        logging.info("Processo concluído com sucesso.")
    else:
        logging.error("Processo encerrado com erros ou cancelado.")

if __name__ == "__main__":
    main()
