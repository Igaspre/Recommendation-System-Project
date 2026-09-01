from .models import Item, Preference, Rating

NUM_PREFERENCES = 115

DEMOGRAPHIC_VECTORS = {
    "joven_hombre_sin_hijos": {
        # Preferencias de primer nivel y/o subnivel:
        3: 70,   # Museos
        9: 65,   # Deportes
        11: 50,  # Ocio
        14: 0,   # Niños (sin hijos => 0)
        28: 60,  # Parques
        34: 70,  # Paseos
        37: 80,  # Cines
        39: 60,  # Conciertos y música en vivo
        62: 70,  # Arte
        63: 80,  # Ciencia y tecnología
        64: 60,  # Historia
        65: 30,  # Religión
        67: 50,  # Arqueología
        68: 50,  # Historia y cultura local
        69: 40,  # Artesanía
        70: 30,  # Militar
    },
    "joven_mujer_sin_hijos": {
        # ~15-20 prefs
        3: 80,   # Museos
        11: 60,  # Ocio
        4: 70,   # Espacios Abiertos
        28: 65,  # Parques
        29: 60,  # Jardines botánicos
        37: 75,  # Cines
        38: 65,  # Teatros
        39: 70,  # Conciertos y música en vivo
        45: 50,  # Restaurantes (gastronomía)
        46: 30,  # Eventos gastronomicos
        63: 80,  # Ciencia y tecnología
        64: 70,  # Historia
        67: 55,  # Arqueología
        68: 60,  # Historia y cultura local
        69: 50,  # Artesanía
        93: 50,  # Centro histórico
    },
    "adulto_hombre_sin_hijos": {
        7: 70,   # Arquitectura civil
        3: 60,   # Museos
        9: 55,   # Deportes
        8: 60,   # Gastronomía
        13: 60,  # Eventos
        34: 60,  # Paseos
        37: 50,  # Cines
        39: 50,  # Conciertos y música en vivo
        62: 50,  # Arte
        64: 50,  # Historia
        66: 40,  # Ciencias naturales
        67: 50,  # Arqueología
        68: 60,  # Historia y cultura local
        69: 50,  # Artesanía
        70: 40,  # Militar
        103: 50, # Estadios y áreas deportivas
    },
    "adulto_mujer_sin_hijos": {
        3: 60,   # Museos
        4: 70,   # Espacios Abiertos
        7: 60,   # Arquitectura civil
        8: 60,   # Gastronomía
        34: 70,  # Paseos
        45: 70,  # Restaurantes
        46: 60,  # Eventos gastronomía
        50: 60,  # Exposiciones
        62: 60,  # Arte
        64: 70,  # Historia
        67: 40,  # Arqueología
        68: 50,  # Historia y cultura local
        69: 60,  # Artesanía
        70: 30,  # Militar
        94: 50,  # Ateneo
        96: 50,  # Edificios académicos
    },
    "familia_hijos_pequenos": {
        14: 90,  # Niños
        11: 70,  # Ocio
        28: 80,  # Parques
        29: 70,  # Jardines botánicos
        30: 90,  # Parque infantil
        4: 60,   # Espacios abiertos
        31: 70,  # Playas
        35: 60,  # Parques temáticos
        37: 70,  # Cines
        39: 60,  # Conciertos y música en vivo
        54: 50,  # Fiestas
        68: 40,  # Historia y cultura local
        86: 30,  # Colegiata (ejemplo)
        90: 20,  # Puertas (algo muy secundario)
        110: 20, # Otras defensivas
    },
    "familia_hijos_adolescentes": {
        13: 80,  # Eventos
        9: 75,   # Deportes
        37: 70,  # Cines
        39: 70,  # Conciertos y música en vivo
        35: 65,  # Parques temáticos
        4: 60,   # Espacios abiertos
        31: 60,  # Playas
        32: 50,  # Lagos
        33: 50,  # Calles y plazas
        60: 50,  # Baloncesto
        61: 50,  # Otros deportes
        68: 40,  # Historia y cultura local
        69: 30,  # Artesanía
        72: 20,  # Catedrales
        73: 20,  # Iglesias
    },
    "adulto_mayor_hombre": {
        5: 70,   # Arquitectura religiosa
        3: 60,   # Museos
        64: 70,  # Historia
        28: 70,  # Parques
        34: 70,  # Paseos
        29: 60,  # Jardines botánicos
        12: 60,  # Salud y SPA
        63: 50,  # Ciencia y tecnología
        67: 60,  # Arqueologia
        68: 60,  # Historia y cultura local
        72: 60,  # Catedrales
        73: 50,  # Iglesias
        75: 40,  # Monasterios
        78: 40,  # Mezquitas
        79: 30,  # Campanarios
    },
    "adulto_mayor_mujer": {
        5: 80,   # Arquitectura religiosa
        3: 60,   # Museos
        28: 70,  # Parques
        34: 70,  # Paseos
        29: 60,  # Jardines botánicos
        12: 60,  # Salud y SPA
        64: 70,  # Historia
        67: 50,  # Arqueología
        68: 60,  # Historia y cultura local
        72: 60,  # Catedrales
        73: 40,  # Iglesias
        75: 40,  # Monasterios
        78: 40,  # Mezquitas
        79: 30,  # Campanarios
        84: 20,  # Basílica
        85: 20,  # Capilla
    },
    "otro": {
        3: 50,   # Museos
        16: 40,  # Prehistórico
        18: 40,  # Romano
        19: 40,  # Medieval
        20: 30,  # Gótico
        21: 30,  # Románico
        22: 30,  # Renacentista
        25: 30,  # Neoclásico
        27: 50,  # Contemporáneo
        63: 50,  # Ciencia y tecnología
        64: 50,  # Historia
        67: 40,  # Arqueologia
        68: 40,  # Historia y cultura local
        8: 50,   # Gastronomía
        11: 50,  # Ocio
        9: 50,   # Deportes
    },
    # 8. Ejecutivo de negocios
    "ejecutivo_negocios": {
        51: 90,   # Conferencias
        52: 85,   # Ferias
        53: 80,   # Congresos
        96: 65,   # Edificios gubernamentales
        97: 60,   # Edificios académicos
        4:  40,   # Espacios Abiertos
        38: 50,   # Teatros
        39: 55,   # Conciertos y música en vivo
        11: 45,   # Ocio
        12: 60,   # Salud y SPA
        95: 45,   # Mercados
        49: 50,   # Otras compras
        45: 70,   # Restaurantes
        46: 55,   # Eventos gastronómicos
        63: 75,   # Ciencia y tecnología
    },
    # 10. Eco-turista
    "eco_turista": {
        28: 85,   # Parques
        29: 80,   # Jardines botánicos
        32: 70,   # Lagos
        31: 65,   # Playas
        4:  90,   # Espacios Abiertos
        34: 75,   # Paseos
        36: 60,   # Otros espacios abiertos
        66: 70,   # Ciencias naturales
        62: 50,   # Arte
        69: 65,   # Artesanía
        48: 55,   # Tiendas tradicionales
        57: 60,   # Náuticos
        11: 50,   # Ocio
        33: 45,   # Calles y plazas
        95: 55,   # Mercados
    },
}

# Clasificar por tipo de usuario
def get_demographic_type(user):
    # 1) Familias con hijos (prioritario sobre ocupación):
    if user.sons > 0:
        if user.younger_son_age <= 12:
            return "familia_hijos_pequenos"
        else:
            return "familia_hijos_adolescentes"

    # 2) Segmentos basados en ocupación:
    #    2 -> Dirección / ejecutivos
    if user.occupation == 2:
        return "ejecutivo_negocios"
    #    3 -> Técnicos y profesionales científicos e intelectuales
    if user.occupation == 3:
        return "profesional_ct"
    #    6 -> Servicios de restauración, protección y ventas
    if user.occupation == 6:
        return "amante_gastronomia"
    #    7 -> Agricultura y pesca (naturaleza -> eco)
    if user.occupation == 7:
        return "eco_turista"

    # 3) Personas mayores de 65
    if user.age >= 65:
        return "adulto_mayor_hombre" if user.gender == 'M' else "adulto_mayor_mujer"

    # 4) Jóvenes vs adultos sin hijos
    if user.age < 35:
        return "joven_hombre_sin_hijos" if user.gender == 'M' else "joven_mujer_sin_hijos"
    else:
        return "adulto_hombre_sin_hijos" if user.gender == 'M' else "adulto_mujer_sin_hijos"

# Construcción del vector final
def build_demographic_preference_vector(user):
    # Obtenemos el "tipo" y su diccionario
    user_type = get_demographic_type(user)
    base_dict = DEMOGRAPHIC_VECTORS.get(user_type, DEMOGRAPHIC_VECTORS["otro"])

    # Mapeo de la taxonomía 
    parent_map = build_taxonomy_map()

    # Creamos el dict pref->interest con los datos base
    pref_interest = dict(base_dict)  

    all_level1 = get_level1_prefs()
    for p_id in all_level1:
        if p_id not in pref_interest or pref_interest[p_id] <= 0:
            continue

        # Chequeamos sus hijos
        children = parent_map.get(p_id, [])
        # Revisamos si algún hijo ya está en pref_interest con valor > 0
        sub_with_interest = [c for c in children if c in pref_interest and pref_interest[c] > 0]

        if not children:
            continue

        if len(sub_with_interest) == 0:
            # Ningún hijo tiene valor => todos heredan
            parent_val = pref_interest[p_id]
            for c in children:
                # Si no existe en el dict, lo ponemos
                if c not in pref_interest or pref_interest[c] == 0:
                    pref_interest[c] = parent_val
        else:
            # Al menos un hijo está puntuado => ignoramos padre
            pref_interest[p_id] = 0  # anulamos la preferencia de nivel 1

    # Construimos el vector final
    final_vector = [0]*NUM_PREFERENCES
    for (pid, interest) in pref_interest.items():
        if pid >= 1 and pid <= NUM_PREFERENCES:
            final_vector[pid - 1] = interest

    return final_vector


def build_taxonomy_map():
    prefs = Preference.query.all()
    parent_map = {}
    for p in prefs:
        if p.parent_id is not None:
            parent = p.parent_id
            if parent not in parent_map:
                parent_map[parent] = []
            parent_map[parent].append(p.id)
    return parent_map

def get_level1_prefs():
    prefs = Preference.query.filter_by(parent_id=None).all()
    return [p.id for p in prefs]

# Funciones de recomendación
def compute_user_item_ratio(item, demographic_vector):
    total = 0
    count = 0
    for classif in item.classifications:
        # Preferencia del usuario por la categoria
        sc = demographic_vector[classif.preference_id - 1]
        if sc > 0:
            # Preferencia por idoneidad de la categroia
            total += classif.weight * sc
            count += 1
    if count == 0:
        return 0
    # Promedio de contribuciones
    ratio = total / count / 10 
    # Bonus de popularidad 
    ratio += 0.05 * item.visit_count
    return ratio

def get_items_recommendation(user, n=10, all=False):
    demographic_vector = build_demographic_preference_vector(user)

    # Excluir vistos
    seen_ids = set()
    user_ratings = Rating.query.filter_by(user_id=user.id, dataset='base').all()
    seen_ids = {r.item_id for r in user_ratings}

    # Recorrer ítems
    all_items = Item.query.all()
    results = []
    for it in all_items:
        if it.id in seen_ids:
            continue
        ratio = compute_user_item_ratio(it, demographic_vector)
        results.append((it, ratio))
    
    # Normalización min-max a un rango de 0 a 100:
    if results:
        scores = [ratio for _, ratio in results]
        min_ratio = min(scores)
        max_ratio = max(scores)
        if max_ratio > min_ratio:
            results = [
                (it, round(((ratio - min_ratio) / (max_ratio - min_ratio)) * 100, 2))
                for it, ratio in results
            ]
        else:
            # Si todos los scores son iguales, asignar 100 a cada uno
            results = [(it, 100) for it, ratio in results]

    # Ordenar y top n
    results.sort(key=lambda x: x[1], reverse=True)
    if not all:
        return results[:n]
    else:
        return results
