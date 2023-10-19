import pandas as pd
from funciones import *
from itertools import combinations
from ortools.linear_solver import pywraplp

# Ubicación de origen
origen = "Avenida Las Rosas 190, San Nicolas, Santa Fe, Argentina"

# Paridad mínima deseada
paridad_minima = 0.25

try:
    # Cargar el archivo Excel
    df = pd.read_excel("datos.xlsx", engine="openpyxl")

    # Obtener la lista de destinos desde el DataFrame
    destinos = df["Destino"].tolist()

    if "Destino" in df.columns:

        df["Destinos de Paso"] = "No tiene"
        # Crear columnas para "Cantidad de Litros", "Distancia (KM)", "Costo en Dólares", "Costo por Litro" y "Eficiente"
        df["Distancia (KM)"] = 0.0
        df["Costo en Pesos"] = 0.0
        df["Costo en Dólares"] = 0.0
        df["Paridad"] = 0.0
        
        df["Eficiente"] = "No"  # Por defecto, se asume que no es eficiente

        # Iterar a través de las filas y calcular las cantidades y costos
        for index, row in df.iterrows():
            destino_actualizado = row["Destino"]
            litros = row["Cantidad de Litros"]
            # URL de la API de MapQuest para calcular la distancia
            url = f"http://www.mapquestapi.com/directions/v2/route?key={api_key}&from={origen}&to={destino_actualizado}"

            # Realizar la solicitud a la API
            response = requests.get(url)
            data = response.json()

            # Verificar si se obtuvo una distancia válida
            if "route" in data and "distance" in data["route"]:
                # Distancia en kilómetros
                distancia_km = data["route"]["distance"] * 1.60934  # Convertir millas a kilómetros
                df.at[index, "Distancia (KM)"] = distancia_km

                # Cantidad de litros (asumimos 20,000 litros por viaje)

                # Costo del flete en pesos
                costo_pesos = 580 * distancia_km  # Tarifa de 580 pesos Argentinos por KM
                df.at[index, "Costo en Pesos"] = costo_pesos

                # Costo del flete en dólares
                costo_dolares = costo_pesos / 350  # Tipo de cambio de 350 pesos por dólar
                df.at[index, "Costo en Dólares"] = costo_dolares

                # Costo por litro
                costo_por_litro = costo_dolares / litros
                df.at[index, "Paridad"] = costo_por_litro

                # Verificar si es eficiente
                if costo_por_litro <= 0.15:
                    df.at[index, "Eficiente"] = "Sí"

                print(f"Distancia entre {origen} y {destino_actualizado}: {distancia_km:.2f} km")
            else:
                print(f"No se pudo obtener la distancia para {origen} y {destino_actualizado}")

        # Calcular si es eficiente realizar varios viajes en una ruta
        es_eficiente, distancias = rutas_en_camino(origen, destinos, paridad_minima)

        # Inicializar un diccionario para rutas de paso
        rutas_de_paso = {}

        # Calcular las distancias entre todos los destinos
        distancias_entre_destinos = {}

        for i in range(len(destinos)):
            for j in range(i + 1, len(destinos)):
                # Obtener la distancia entre origen y destino
               
                distancia = calcular_distancia(origen, destinos[i])
                distancia_entre_destino = calcular_distancia(destinos[i], destinos[j])

                if distancia is not None and distancia_entre_destino is not None:
                    distancias_entre_destinos[(i, j)] = distancia_entre_destino
                    distancias_entre_destinos[(j, i)] = distancia_entre_destino
                    print("Distancia entre", destinos[i], "y", destinos[j], ":", distancia_entre_destino)

        # Verificar si alguna de las rutas puede quedar de paso hacia otra
        for i in range(len(destinos)):
            for j in range(len(destinos)):
                if i != j:
                    paridad_i = df["Paridad"][i]
                    paridad_j = df["Paridad"][j]
                    paridad_ij = paridad_i / paridad_j
                    if paridad_ij <= paridad_minima:
                        # Verificar si el destino j queda de paso hacia destino i
                        destinos_de_paso = []
                        for k in range(len(destinos)):
                            if k != i and k != j:
                                distancia_ik = distancias_entre_destinos[(i, k)]
                                distancia_kj = distancias_entre_destinos[(k, j)]
                                distancia_ij = distancias_entre_destinos[(i, j)]

                                if distancia_ik + distancia_kj <= distancia_ij:
                                    destinos_de_paso.append(destinos[k])

                        if destinos_de_paso:
                            if i not in rutas_de_paso:
                                rutas_de_paso[i] = []
                            rutas_de_paso[i].append((j, destinos_de_paso))

        # Verificar si es eficiente agregar rutas de paso
    rutas_a_agregar = []
    for i in rutas_de_paso:
        for j, destinos_paso in rutas_de_paso[i]:
            paridad_paso = sum([df["Paridad"][i], df["Paridad"][j]] + [df["Paridad"][destinos.index(destino)] for destino in destinos_paso])

            if paridad_paso <= paridad_minima:
                rutas_a_agregar.append((i, j, destinos_paso))
                
    # Actualizar las columnas "Destinos de Paso" y "Paridad Total" en el DataFrame
    print("Rutas de paso encontradas:", rutas_de_paso)

    for i, j, destinos_paso in rutas_a_agregar:
        destinos_paso_str = '; '.join(destinos_paso)
        df.at[i, "Destinos de Paso"] = destinos_paso_str
        print("Destinos de paso a MOVIPORT San Nicolás: ", destinos_paso_str)
        df.at[i, "Paridad Total"] = df["Paridad"][i] + df["Paridad"][j]



    ubicacion_aproximada = obtener_coordenadas_direccion(origen)
    if ubicacion_aproximada:
        rutas_cercanas = []

        for i in range(len(destinos)):
            distancia = calcular_distancia(origen, destinos[i])
            if distancia is not None and distancia <= 20:
                rutas_cercanas.append(destinos[i])
    else:
        print("Error: No se pudieron obtener las coordenadas de la ubicación aproximada.")

    # Guardar los cambios en el archivo Excel original
    df.to_excel("datos.xlsx", index=False)  # Esto sobrescribirá el archivo Excel con los cambios
    print("Cálculos realizados y guardados en el archivo 'datos.xlsx'")

except Exception as e:
    print("Ocurrió un error:", str(e))