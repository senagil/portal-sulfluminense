import feedparser
import requests
import sqlite3
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

# ---------------------- CONFIGURAÇÕES ----------------------
FEEDS = {
    "G1 RJ": "https://g1.globo.com/rj/feed/rss2.xml",
    "O Dia": "https://www.odia.com.br/rss/noticias/rj.xml",
    "Extra RJ": "https://extra.globo.com/rss/rj.xml",
    "O Globo RJ": "https://oglobo.globo.com/rss/rj.xml"
}

CIDADE_PRIORIDADE_1 = [
    "Barra Mansa", "Volta Redonda", "Resende", "Itatiaia",
    "Barra do Piraí", "Porto Real", "Piraí", "Pinheiral", "Angra dos Reis"
]
CIDADE_PRIORIDADE_2 = [
    "Rio de Janeiro", "Niterói", "São Gonçalo", "Duque de Caxias",
    "Nova Iguaçu", "Petrópolis", "Teresópolis", "Araruama", "Cabo Frio"
]

PALAVRAS_CHAVE_SUL = [c.lower() for c in CIDADE_PRIORIDADE_1]
PALAVRAS_CHAVE_RJ = [c.lower() for c in CIDADE_PRIORIDADE_2]

BANCO = "noticias.db"
ARQUIVO_SAIDA = "../frontend/dados_noticias.json"
PERIODICIDADE_MIN = 20
# -----------------------------------------------------------

def init_banco():
    conn = sqlite3.connect(BANCO)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL UNIQUE,
            resumo TEXT,
            imagem_url TEXT,
            fonte_origem TEXT,
            url_original TEXT UNIQUE,
            categoria TEXT,
            cidade_tag TEXT,
            data_publicacao TIMESTAMP,
            score_relevancia REAL DEFAULT 0.0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def classificar_noticia(texto):
    """Retorna (cidade_tag, score) com base em palavras-chave"""
    texto = texto.lower()
    for cidade in PALAVRAS_CHAVE_SUL:
        if re.search(rf"\b{re.escape(cidade)}\b", texto):
            return cidade.title(), 10.0
    for cidade in PALAVRAS_CHAVE_RJ:
        if re.search(rf"\b{re.escape(cidade)}\b", texto):
            return "Estado do Rio de Janeiro", 5.0
    return "Brasil", 1.0

def extrair_imagem(summary):
    """Busca primeira tag <img> no resumo e retorna a URL"""
    soup = BeautifulSoup(summary, "html.parser")
    img = soup.find("img")
    return img.get("src") if img else ""

def ja_existe(url):
    conn = sqlite3.connect(BANCO)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM noticias WHERE url_original = ?", (url,))
    existe = cur.fetchone() is not None
    conn.close()
    return existe

def salvar_noticia(dados):
    conn = sqlite3.connect(BANCO)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO noticias
            (titulo, resumo, imagem_url, fonte_origem, url_original,
             categoria, cidade_tag, data_publicacao, score_relevancia)
            VALUES (:titulo, :resumo, :imagem_url, :fonte_origem, :url_original,
                    :categoria, :cidade_tag, :data_publicacao, :score_relevancia)
        """, dados)
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # duplicado — ignora
    conn.close()

def exportar_json():
    """Gera JSON consumível pelo frontend"""
    conn = sqlite3.connect(BANCO)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM noticias
        ORDER BY score_relevancia DESC, data_publicacao DESC
        LIMIT 150
    """)
    dados = []
    for linha in cur.fetchall():
        linha_dict = dict(linha)
        # Converte data para formato amigável
        dt = linha_dict["data_publicacao"]
        try:
            data_obj = date_parser.parse(dt)
            linha_dict["data_formatada"] = data_obj.strftime("%d/%m/%Y %H:%M")
        except:
            linha_dict["data_formatada"] = dt
        dados.append(linha_dict)
    conn.close()

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def executar():
    print(f"🔄 Iniciando coleta — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    init_banco()

    for nome_fonte, url_feed in FEEDS.items():
        try:
            feed = feedparser.parse(url_feed)
            for entrada in feed.entries[:15]:  # limita por fonte
                titulo = entrada.title.strip()
                resumo = getattr(entrada, "summary", "")
                url = entrada.link
                if ja_existe(url):
                    continue
                data_pub = getattr(entrada, "published", datetime.now().isoformat())
                imagem = extrair_imagem(resumo)
                texto_completo = f"{titulo} {resumo}"
                cidade_tag, score = classificar_noticia(texto_completo)

                dados_noticia = {
                    "titulo": titulo,
                    "resumo": BeautifulSoup(resumo, "html.parser").get_text()[:280] + "...",
                    "imagem_url": imagem,
                    "fonte_origem": nome_fonte,
                    "url_original": url,
                    "categoria": "Geral",
                    "cidade_tag": cidade_tag,
                    "data_publicacao": data_pub,
                    "score_relevancia": score
                }
                salvar_noticia(dados_noticia)
            print(f"✅ {nome_fonte} processado")
        except Exception as e:
            print(f"⚠️ Erro em {nome_fonte}: {e}")

    exportar_json()
    print("📄 JSON exportado para frontend/dados_noticias.json")
    print("✅ Coleta finalizada\n")

if __name__ == "__main__":
    executar()