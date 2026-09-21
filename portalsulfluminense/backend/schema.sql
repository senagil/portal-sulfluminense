CREATE TABLE IF NOT EXISTS noticias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    resumo TEXT,
    imagem_url TEXT,
    fonte_origem TEXT NOT NULL,
    url_original TEXT UNIQUE NOT NULL,
    categoria TEXT,
    cidade_tag TEXT,
    data_publicacao TIMESTAMP,
    score_relevancia REAL DEFAULT 0.0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);