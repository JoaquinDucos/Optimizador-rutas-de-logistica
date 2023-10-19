import pandas as pd
from funciones import *
from itertools import combinations
from ortools.linear_solver import pywraplp
df = pd.read_excel("datos.xlsx", engine="openpyxl")
  # Obtener la lista de destinos desde el DataFrame
destinos = df["Destino"].tolist()
for index, row in df.iterrows():
    destino_actualizado = row["Destino"]
    litros = row["Cantidad de Litros"]
    print(litros)