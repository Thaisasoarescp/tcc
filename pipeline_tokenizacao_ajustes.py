import json
import re
import unicodedata
from bs4 import BeautifulSoup
import spacy 
import emoji
import nltk
from nltk.stem import RSLPStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

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


nome_arquivo_entrada = r"G:\Meu Drive\Tcc\dados\noticias_desastres_jp.csv"

try:
    df = pd.read_csv(nome_arquivo_entrada, encoding="utf-8")
    noticias = df.to_dict(orient="records")
    print(f" Arquivo '{nome_arquivo_entrada}' carregado! ({len(noticias)} notícias)\n")
except FileNotFoundError:
    print(f" ERRO: O arquivo '{nome_arquivo_entrada}' não foi encontrado.")
    exit()
except Exception as e:
    print(f" ERRO ao carregar CSV: {e}")
    exit()

# ---------------------------------------------------------
# FUNÇÕES DA PIPELINE (MELHORADAS PARA MOSTRAR ETAPAS)
# ---------------------------------------------------------

def limpar_html_e_lixo(texto):
    """Etapa 1: Remove HTML, URLs e menções."""
    texto = str(texto)
    texto = BeautifulSoup(texto, "html.parser").get_text()
    texto = re.sub(r'http\S+|www\S+|https\S+', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'@\w+', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def normalizar_texto(texto):
    """Etapa 2: Minúsculas e emojis."""
    texto = str(texto)
    texto = texto.lower()
    # Substitui Emojis e Números
    texto = emoji.replace_emoji(texto, replace='[EMOJI]')
    return texto

def processar_pipeline_completa(texto_original):
    """Executa e armazena cada etapa do processo de NLP."""
    
    # ETAPA 1: Limpeza Inicial
    texto_limpo = limpar_html_e_lixo(texto_original)

    # ETAPA 2: Normalização Geral (do texto todo para visualização)
    texto_normalizado = normalizar_texto(texto_limpo)
    
    # ETAPA 3: Processamento SpaCy
    doc = nlp(texto_limpo)

    #ETAPA 4: Extração das entiades
    entidades = [{  
                    "texto": ent.text,
                    "tipo": ent.label_
                } 
                    for ent in doc.ents]
    
    
    
    # ETAPA 5: Tokenização, Stopwords e Lemmatização
    tokens_finais = []
    detalhes_tokens = [] # Para ver o que era e o que virou
    
    for token in doc:
        #Ignorando espaços e pontuação
        if token.is_punct or token.is_space:
            continue
        # Pegamos o lemma (raiz da palavra pelo SpaCy) e normalizamos
        termo = token.lemma_.lower().strip()

        if not termo:
            continue

        
        tokens_finais.append(termo)
        detalhes_tokens.append({"original": token.text, "processado": termo})
                
    # ETAPA 6: Texto Final para IA
    texto_final_ia = " ".join(tokens_finais)
    
    return {
         "etapa_1_limpeza": texto_limpo,
         "etapa_2_normalizacao": texto_normalizado,
         "etapa_3_entidades": entidades,
         "etapa_4_tokens": detalhes_tokens,
         "etapa_5_lista_tokens": tokens_finais,
         "etapa_6_texto_final": texto_final_ia
    }

# ---------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------

dados_finais = []
textos_para_tfidf = []

for i, noticia in enumerate(noticias):
    print(f"[{i+1}/{len(noticias)}] Processando: {noticia.get('titulo', 'Sem título')[:50]}...")
    
    titulo = noticia.get('titulo', '')
    print(f"[{i+1}/{len(noticias)}] Processando: {titulo[:50]}...")
    if not titulo:
        continue
        
    # Chama a pipeline que retorna o dicionário com todas as etapas
    resultado_pipeline = processar_pipeline_completa(titulo)
    
    # Adiciona à lista do TF-IDF
    textos_para_tfidf.append(resultado_pipeline["etapa_6_texto_final"])
    
    # Monta o objeto final da notícia
    noticia_enriquecida = {
        "id": i + 1,
        "site": noticia.get("site"),
        "data": noticia.get("data"),
        "titulo_original": titulo,
        "url": noticia.get("url"),
        "pipeline_nlp": resultado_pipeline # Aqui estão todas as etapas salvas
    }
    
    dados_finais.append(noticia_enriquecida)

# ---------------------------------------------------------
# TF-IDF E SALVAMENTO
# ---------------------------------------------------------

# Gerar vocabulário TF-IDF
if textos_para_tfidf:
    vectorizer = TfidfVectorizer(max_df=0.95, min_df=2)
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
print(f" CONCLUÍDO!")
print(f" O arquivo 'noticias_processadas_etapas.json' contém cada passo do processamento.")
print("="*50)