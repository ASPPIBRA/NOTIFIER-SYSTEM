"""
gemini_media.py

Script para consultar e coletar informações sobre jornais, portais de notícias e blogs relacionados a criptomoedas
em qualquer país, utilizando a API Gemini (Google AI).

Autor: [Seu Nome]
Data: 2025
"""

import json
import requests

# Insira sua chave da API Gemini aqui
API_KEY = "SUA_CHAVE_DA_API_GEMINI"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

# Consulta à API Gemini com um prompt customizado
def consultar_api_gemini(prompt):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        response = requests.post(f"{ENDPOINT}?key={API_KEY}", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"[ERRO] Falha na consulta à API Gemini: {e}")
        return None

# Coleta de dados para o país especificado
def coletar_dados_crypto_pais(pais):
    dados = {
        "pais": pais,
        "jornais": [],
        "portais_de_noticias": [],
        "blogs_e_sites_independentes": []
    }

    # Prompts dinâmicos por país
    prompts = {
        "jornais": f"Liste os principais jornais de {pais} que já publicaram matérias sobre criptomoedas. Inclua nome, cidade, URL, email, telefone e endereço, se disponível. Formato JSON.",
        "portais_de_noticias": f"Liste portais de notícias digitais de {pais} voltados para fintechs e criptomoedas. Formato JSON com nome, cidade, URL, email, telefone e endereço.",
        "blogs_e_sites_independentes": f"Liste blogs ou sites independentes de {pais} que tratam de criptomoedas. Responda em JSON estruturado com nome, cidade, URL, email, telefone e endereço se houver."
    }

    for categoria, prompt in prompts.items():
        print(f"[INFO] Consultando API Gemini para categoria: {categoria} ({pais})...")
        resposta = consultar_api_gemini(prompt)
        if resposta:
            try:
                dados_extraidos = json.loads(resposta)
                if isinstance(dados_extraidos, list):
                    dados[categoria] = dados_extraidos
                    print(f"[SUCESSO] {len(dados_extraidos)} registros adicionados à categoria '{categoria}'.")
                else:
                    print(f"[AVISO] Resposta inesperada da Gemini para {categoria}.")
            except json.JSONDecodeError:
                print(f"[ERRO] Falha ao interpretar JSON para categoria {categoria}.")
        else:
            print(f"[FALHA] Nenhuma informação obtida para categoria '{categoria}'.")

    return dados

# Execução principal
if __name__ == "__main__":
    pais = input("Digite o nome do país que deseja consultar (ex: Nigéria, Brasil, Índia): ").strip()
    if not pais:
        print("[ERRO] País não informado. Encerrando execução.")
    else:
        dados_coletados = coletar_dados_crypto_pais(pais)

        nome_arquivo = f"crypto_media_{pais.lower().replace(' ', '_')}.json"
        try:
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                json.dump(dados_coletados, f, indent=2, ensure_ascii=False)
            print(f"[FINALIZADO] Dados salvos com sucesso em '{nome_arquivo}'")
        except Exception as e:
            print(f"[ERRO] Falha ao salvar o arquivo: {e}")
