import requests
from bs4 import BeautifulSoup
import time
import pandas as pd

URL = "https://jovempan.com.br/noticias/brasil/page/{}"

headers = {
    "User-Agent": "Mozilla/5.0"
}
palavras_chave = [
    "chuva", "enchente", "alagamento", "deslizamento",
    "tempestade", "ciclone", "furacão", "seca",
    "incêndio", "queimada", "desastre", "tragédia"
]

dados = []

for pagina in range(1, 20):  
    
    url = URL.format(pagina)
    print(f"Coletando página {pagina}...")

    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print("Erro na página:", pagina)
            break
        
        soup = BeautifulSoup(response.text, "html.parser")

        # pega todos os links da página
        noticias = soup.find_all("article")

        for noticia in noticias:
            titulo_tag = noticia.find("h2", class_="post-title")
            if titulo_tag:
                link_tag = titulo_tag.find("a")
            else:
                link_tag = None
            titulo = link_tag.get_text(strip=True) if link_tag else None
            link = link_tag.get("href") if link_tag else None
            data_tag = noticia.find("span", class_="date")
            data = data_tag.get_text(strip=True) if data_tag else None

            if titulo and link:
                titulo_lower = titulo.lower()

                # filtro por palavras-chave
                if any(p in titulo_lower for p in palavras_chave):
                    dados.append({
                        "titulo": titulo,
                        "link": link,
                        "data": data
                    })

    except Exception as e:
        print("Erro:", e)


    time.sleep(5)


df = pd.DataFrame(dados).drop_duplicates()

df.to_csv("noticias_desastres_jp.csv", index=False, encoding="utf-8-sig")

print("Finalizado! Total coletado:", len(df))
