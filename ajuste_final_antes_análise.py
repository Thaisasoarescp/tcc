import pandas as pd
from matplotlib import pyplot as plt

df = pd.read_csv(r"G:\Meu Drive\Tcc\dados\noticias_desastres_jp.csv")

print(df.head(100))
df["site"] = "Jovem Pan"
print(df.head(100))
df["data"] = pd.to_datetime(
    df["data"],
    format="%d/%m/%Y %Hh%M"
)

print(df["data"].dtype)

print(df["data"])


noticias_por_ano = (
    df.groupby(df["data"].dt.year)
      .size()
      .reset_index(name="quantidade_noticias")
)

noticias_por_ano.plot(
    x="data",
    y="quantidade_noticias",
    kind="bar"
)

plt.xlabel("Ano")
plt.ylabel("Quantidade de Notícias")
plt.title("Notícias por Ano")

df.to_csv(r"G:\Meu Drive\Tcc\dados\noticias_desastres_jp.csv")