import json
import re
import unicodedata
from bs4 import BeautifulSoup
import emoji
import spacy
import nltk
from nltk.stem import RSLPStemmer
from sklearn.feature_extraction.text import TfidfVectorizer

# ---------------------------------------------------------
# CONFIGURAÇÕES INICIAIS
# ---------------------------------------------------------
nltk.download('rslp', quiet=True)

try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    print("❌ Erro: Modelo 'pt_core_news_sm' não encontrado. Execute: python -m spacy download pt_core_news_sm")
    exit()

stemmer = RSLPStemmer()

# ---------------------------------------------------------
# CARREGANDO OS DADOS
# ---------------------------------------------------------
nome_arquivo_entrada = "noticias_com_conteudo.json"

try:
    with open(nome_arquivo_entrada, "r", encoding="utf-8") as arquivo_leitura:
        noticias = json.load(arquivo_leitura)
    print(f"✅ Arquivo '{nome_arquivo_entrada}' carregado! ({len(noticias)} notícias)\n")
except FileNotFoundError:
    print(f"❌ ERRO: O arquivo '{nome_arquivo_entrada}' não foi encontrado.")
    exit()

# ---------------------------------------------------------
# FUNÇÕES DA PIPELINE (MELHORADAS PARA MOSTRAR ETAPAS)
# ---------------------------------------------------------

def limpar_html_e_lixo(texto):
    """Etapa 1: Remove HTML, URLs e menções."""
    texto = BeautifulSoup(texto, "html.parser").get_text()
    texto = re.sub(r'http\S+|www\S+|https\S+', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'@\w+', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def normalizar_texto(texto):
    """Etapa 2: Minúsculas, acentos, emojis e números."""
    texto = texto.lower()
    # Remove acentos
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    # Substitui Emojis e Números
    texto = emoji.replace_emoji(texto, replace='[EMOJI]')
    texto = re.sub(r'r\$\s*\d+(?:[.,]\d+)*', '[MOEDA]', texto)
    texto = re.sub(r'\b\d+(?:[.,]\d+)*\b', '[NUMERO]', texto)
    return texto

def processar_pipeline_completa(texto_original):
    """Executa e armazena cada etapa do processo."""
    
    # ETAPA 1: Limpeza Inicial
    texto_limpo = limpar_html_e_lixo(texto_original)
    
    # ETAPA 2: Extração de Entidades (feita antes da normalização agressiva)
    doc = nlp(texto_limpo)
    entidades = [{"texto": ent.text, "tipo": ent.label_} for ent in doc.ents]
    
    # ETAPA 3: Normalização Geral (do texto todo para visualização)
    texto_normalizado = normalizar_texto(texto_limpo)
    
    # ETAPA 4: Tokenização, Stopwords e Lemmatização
    tokens_finais = []
    detalhes_tokens = [] # Para ver o que era e o que virou
    
    for token in doc:
        # Filtros: pontuação, espaços e palavras vazias (stop words)
        if not token.is_stop and not token.is_punct and not token.is_space:
            # Pegamos o lemma (raiz da palavra pelo SpaCy) e normalizamos
            termo = normalizar_texto(token.lemma_)
            if termo:
                tokens_finais.append(termo)
                detalhes_tokens.append({"original": token.text, "processado": termo})
                
    # ETAPA 5: Texto Final para IA
    texto_final_ia = " ".join(tokens_finais)
    
    return {
        "etapa_1_limpeza_html": texto_limpo,
        "etapa_2_entidades": entidades,
        "etapa_3_normalizacao_visual": texto_normalizado,
        "etapa_4_tokens_detalhes": detalhes_tokens,
        "etapa_5_lista_tokens_ia": tokens_finais,
        "etapa_6_texto_pronto_ia": texto_final_ia
    }

# ---------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------

dados_finais = []
textos_para_tfidf = []

for i, noticia in enumerate(noticias):
    print(f"[{i+1}/{len(noticias)}] Processando: {noticia.get('titulo', 'Sem título')[:50]}...")
    
    conteudo = noticia.get('conteudo', '')
    if not conteudo:
        continue
        
    # Chama a pipeline que retorna o dicionário com todas as etapas
    resultado_pipeline = processar_pipeline_completa(conteudo)
    
    # Adiciona à lista do TF-IDF
    textos_para_tfidf.append(resultado_pipeline["etapa_6_texto_pronto_ia"])
    
    # Monta o objeto final da notícia
    noticia_enriquecida = {
        "id": i + 1,
        "titulo": noticia.get("titulo"),
        "url": noticia.get("url"),
        "conteudo_original": conteudo,
        "pipeline_nlp": resultado_pipeline # Aqui estão todas as etapas salvas
    }
    
    dados_finais.append(noticia_enriquecida)

# ---------------------------------------------------------
# TF-IDF E SALVAMENTO
# ---------------------------------------------------------

# Gerar vocabulário TF-IDF
if textos_para_tfidf:
    vectorizer = TfidfVectorizer()
    vectorizer.fit(textos_para_tfidf)
    vocabulario = list(vectorizer.get_feature_names_out())
else:
    vocabulario = []

# Salvar Arquivo Principal
with open("noticias_processadas_etapas.json", "w", encoding="utf-8") as f:
    json.dump(dados_finais, f, ensure_ascii=False, indent=4)

# Salvar Vocabulário
with open("vocabulario_tfidf.json", "w", encoding="utf-8") as f:
    json.dump(vocabulario, f, ensure_ascii=False, indent=4)

print("\n" + "="*50)
print(f"✅ CONCLUÍDO!")
print(f"📂 O arquivo 'noticias_processadas_etapas.json' contém cada passo do processamento.")
print("="*50)