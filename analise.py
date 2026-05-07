import pandas as pd
import json
from transformers import pipeline



modelo_sentimento = pipeline(
    "sentiment-analysis",
    model="pysentimiento/robertuito-sentiment-analysis"
)

with open("noticias_processadas_etapas.json", "r", encoding="utf-8") as f:
    noticias = json.load(f)

for noticia in noticias:

    titulo = noticia["titulo_original"]

    resultado = modelo_sentimento(titulo)[0]

    noticia["analise_sentimento"] = {
        "sentimento": resultado["label"],
        "confianca": round(resultado["score"], 4)
    }

df = pd.DataFrame(noticias)

df.to_csv(
    "noticias_com_sentimento.csv",
    index=False,
    encoding="utf-8-sig"
)





