import requests
from geopy.distance import geodesic

# Clave API de MapQuest
api_key = "Tu API KEY DE MapQuest"

def calcular_distancia(origen, destino):
    url = f"http://www.mapquestapi.com/directions/v2/route?key={api_key}&from={origen}&to={destino}"
    response = requests.get(url)
    data = response.json()
    
    if "route" in data and "distance" in data["route"]:
        distancia_km = data["route"]["distance"] * 1.60934  # Convertir millas a kilómetros
        return distancia_km
    else:
        return None

def obtener_coordenadas_ruta(origen, destino):
    url = f"http://www.mapquestapi.com/directions/v2/route?key={api_key}&from={origen}&to={destino}"
    response = requests.get(url)
    data = response.json()
    
    if "route" in data and "locations" in data["route"]:
        coordenadas = [(
            location["displayLatLng"]["lat"],
            location["displayLatLng"]["lng"]
        ) for location in data["route"]["locations"]]
        return coordenadas
    else:
        return None

def obtener_coordenadas_direccion(direccion):
    url = f"http://www.mapquestapi.com/geocoding/v1/address?key={api_key}&location={direccion}"
    response = requests.get(url)
    data = response.json()

    if "results" in data and data["results"]:
        locations = data["results"][0]["locations"]
        if locations:
            latitud = locations[0]["displayLatLng"]["lat"]
            longitud = locations[0]["displayLatLng"]["lng"]
            return [latitud, longitud]  # Devolver como lista
    return None

def rutas_en_camino(origen, destinos, paridad_minima):
    distancias = []

    for destino in destinos:
        distancia = calcular_distancia(origen, destino)
        if distancia is not None:
            distancias.append(distancia)

    es_eficiente = any(distancia <= paridad_minima for distancia in distancias)
    
    return es_eficiente, distancias

def dividir_ruta_en_tramos(origen, destino, numero_tramos=30):
    coordenadas_ruta = []

    url = f"http://www.mapquestapi.com/directions/v2/route?key={api_key}&from={origen}&to={destino}&routeType=fastest&locale=en_US&unit=k&routeType=fastest&outFormat=json&ambiguities=ignore&maxLinkId=1000&drivingStyle=normal&highwayEfficiency=21.0"
    response = requests.get(url)
    data = response.json()

    if "route" in data and "legs" in data["route"]:
        for leg in data["route"]["legs"]:
            for step in leg["maneuvers"]:
                lat, lng = step["startPoint"]["lat"], step["startPoint"]["lng"]
                coordenadas_ruta.append((lat, lng))
    else:
        return None

    tramos = []
    tramo_size = len(coordenadas_ruta) // numero_tramos
    for i in range(0, len(coordenadas_ruta), tramo_size):
        tramo = coordenadas_ruta[i:i + tramo_size]
        tramos.append(tramo)

    return tramos

def verificar_ubicacion_cerca_de_ruta(coordenadas_ruta, ubicacion_aproximada):
    distancia_maxima_km = 20
    if ubicacion_aproximada is not None:
        if isinstance(ubicacion_aproximada, (list, tuple)) and len(ubicacion_aproximada) == 2:
            latitud_aproximada, longitud_aproximada = ubicacion_aproximada
        else:
            raise ValueError("El argumento 'ubicacion_aproximada' debe ser de tipo 'list' o 'tuple' con dos elementos.")

    distancia_km = float(geodesic((0, 0), (latitud_aproximada, longitud_aproximada)).kilometers[0])
    
    if distancia_km != 0:
        raise ValueError("La función 'geodesic()' no está funcionando correctamente.")

    for tramo in coordenadas_ruta:
        for lat, lng in tramo:
            ubicacion_ruta = (lat, lng)
            distancia_km = float(geodesic(ubicacion_ruta, (latitud_aproximada, longitud_aproximada)).kilometers[0])
            if distancia_km <= distancia_maxima_km:
                return True
    return False