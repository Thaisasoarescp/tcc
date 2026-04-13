import requests
from bs4 import BeautifulSoup
import json
import time
import os

# Configurações de arquivos e tempo
ARQUIVO_ENTRADA = 'noticias_jovem_pan_links.json'
ARQUIVO_SAIDA = 'noticias_com_conteudo.json'
TEMPO_ESPERA = 3 # Tempo em segundos entre as requisições

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def carregar_progresso():
    """Carrega o arquivo de saída se ele já existir para não raspar dados duplicados."""
    if os.path.exists(ARQUIVO_SAIDA):
        with open(ARQUIVO_SAIDA, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def salvar_progresso(dados):
    """Salva a lista de dados no arquivo JSON de saída."""
    with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def main():
    # Lendo o arquivo JSON de entrada
    try:
        with open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f:
            links_para_processar = json.load(f)
    except FileNotFoundError:
        print(f"Erro: O arquivo '{ARQUIVO_ENTRADA}' não foi encontrado.")
        return

    # Carregando o que já foi feito (caso o script tenha sido interrompido antes)
    resultados = carregar_progresso()
    
    # Criando uma lista com as URLs que já foram processadas para pularmos
    urls_processadas = [item['url'] for item in resultados]
    
    ultimo_link_processado = None

    print(f"Iniciando scraping. Já existem {len(urls_processadas)} notícias salvas.")

    try:
        for item in links_para_processar:
            url = item['url']
            categoria = item['categoria']

            # Pula a requisição se essa URL já está salva no JSON de saída
            if url in urls_processadas:
                continue

            print(f"Extraindo: {url}")

            # Fazendo a requisição GET
            response = requests.get(url, headers=headers)
            response.raise_for_status() # Lança erro se a página não existir (404, etc)
            
            # Analisando o HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Pegando o Título
            titulo_elemento = soup.find("h1", class_="post-title")
            titulo_scraped = titulo_elemento.get_text(strip=True) if titulo_elemento else item['titulo']
            
            # Pegando o Subtítulo
            subtitulo_elemento = soup.find("h3", class_="post-description")
            subtitulo = subtitulo_elemento.get_text(strip=True) if subtitulo_elemento else ""
            
            # Pegando os parágrafos do conteúdo
            conteudo_div = soup.find("div", class_="context")
            paragrafos = []
            if conteudo_div:
                for p in conteudo_div.find_all("p"):
                    texto_limpo = p.get_text(strip=True)
                    if texto_limpo:
                        paragrafos.append(texto_limpo)
                        
            texto_noticia = "\n\n".join(paragrafos)
            
            # Juntando subtítulo com o conteúdo
            conteudo_final = f"{subtitulo}\n\n{texto_noticia}" if subtitulo else texto_noticia

            # Adicionando o resultado na lista principal
            resultados.append({
                "titulo": titulo_scraped,
                "url": url,
                "categoria": categoria,
                "conteudo": conteudo_final
            })

            ultimo_link_processado = url
            urls_processadas.append(url)

            # Salva o arquivo a cada notícia extraída. 
            # Assim, se cair a energia ou a internet, não perde nada.
            salvar_progresso(resultados)

            # Aguarda o tempo estipulado antes da próxima requisição
            print(f"Sucesso! Aguardando {TEMPO_ESPERA} segundos...")
            time.sleep(TEMPO_ESPERA)

        print("\nProcesso finalizado com sucesso! Todas as notícias foram extraídas.")

    except KeyboardInterrupt:
        # Quando o usuário aperta Ctrl+C para forçar a parada
        print("\n\nScript interrompido pelo usuário!")
        if ultimo_link_processado:
            print(f"O último link salvo com sucesso foi:\n=> {ultimo_link_processado}")
        else:
            print("Nenhum link novo foi processado desta vez.")

    except Exception as e:
        # Quando dá algum erro (caiu internet, página 404, etc)
        print(f"\n\nOcorreu um erro no meio do caminho: {e}")
        if ultimo_link_processado:
            print(f"Progresso salvo! O último link salvo com sucesso foi:\n=> {ultimo_link_processado}")
        else:
            print("Nenhum link novo foi processado antes do erro.")
        print("Você pode rodar o script novamente mais tarde. Ele vai continuar de onde parou.")

if __name__ == "__main__":
    main()