from math import sqrt
from .models import User, Item, Rating, UserPreference

def get_user_vector(user):
    """
    Construye el vector del usuario combinando sus ratings y preferencias.
    Se escalonan las preferencias (multiplicadas por 10) para que sean comparables con los ratings.
    """
    vector = {}
    ratings = Rating.query.filter_by(user_id=user.id, dataset='base').all()
    for r in ratings:
        vector[f"item_{r.item_id}"] = r.rating
    prefs = UserPreference.query.filter_by(user_id=user.id).all()
    for p in prefs:
        # Escalamos para que coincida con los ratings
        vector[f"pref_{p.preference_id}"] = p.interest * 10  
    return vector

def compute_pearson_similarity(vec1, vec2, min_common=5):
    """
    Calcula el coeficiente de correlación de Pearson entre dos vectores.
    
    - Si el número de claves en común (intersección) es al menos 'min_common',
      se usa dicha intersección para el cálculo.
    - En caso contrario, se utiliza la unión de las claves, asumiendo valor 0 en posiciones faltantes.
    """
    common_keys = set(vec1.keys()) & set(vec2.keys())
    if len(common_keys) >= min_common:
        keys = common_keys
    else:
        keys = set(vec1.keys()) | set(vec2.keys())
    
    n = len(keys)
    if n == 0:
        return 0

    sum1 = sum(vec1.get(k, 0) for k in keys)
    sum2 = sum(vec2.get(k, 0) for k in keys)
    sum1_sq = sum((vec1.get(k, 0))**2 for k in keys)
    sum2_sq = sum((vec2.get(k, 0))**2 for k in keys)
    product_sum = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in keys)

    numerator = product_sum - (sum1 * sum2 / n)
    denominator_term1 = sum1_sq - (sum1 ** 2) / n
    denominator_term2 = sum2_sq - (sum2 ** 2) / n
    if denominator_term1 <= 0 or denominator_term2 <= 0:
        return 0
    denominator = sqrt(denominator_term1) * sqrt(denominator_term2)
    if denominator == 0:
        return 0
    return numerator / denominator

def get_collaborative_recommendations(user, top_n=10, n_neighbors=20, min_rating=60, min_common=5, all=False):
    """
    Genera recomendaciones colaborativas basadas en la similitud (Pearson) entre el usuario actual y el resto de usuarios.
    
    Se consideran solo los ítems que no han sido vistos por el usuario y que tienen ratings favorables (>= min_rating).
    Para calcular la similitud se utiliza la función compute_pearson_similarity que emplea intersección o unión según
    la cantidad de elementos compartidos (min_common).
    Se agregan los ratings ponderados por la similitud de cada vecino y se añade un bonus por popularidad (visit_count).
    Finalmente, se normalizan los scores a un rango de 0 a 100 y se devuelven los top_n ítems.
    """
    user_vector = get_user_vector(user)
    if not user_vector:
        # No hay información colaborativa (ni ratings ni preferencias)
        return []
    
    # Ítems ya vistos por el usuario (claves que comienzan con "item_")
    seen_items = {int(key.split("_")[1]) for key in user_vector if key.startswith("item_")}
    
    # Calcular similitud con todos los demás usuarios
    neighbors = []
    all_users = User.query.filter(User.id != user.id).all()
    for other in all_users:
        other_vector = get_user_vector(other)
        if not other_vector:
            continue
        sim = compute_pearson_similarity(user_vector, other_vector, min_common=min_common)
        if sim > 0:
            neighbors.append((other.id, sim, other_vector))
    
    if not neighbors:
        return []
    
    # Ordenar vecinos por similitud descendente y limitar a n_neighbors
    neighbors.sort(key=lambda x: x[1], reverse=True)
    neighbors = neighbors[:n_neighbors]
    
    # Calcular predicción para cada ítem usando los ratings favorables de los vecinos
    recommendations = {}
    for neighbor_id, similarity, neighbor_vector in neighbors:
        # Esto asume que almenos tiene un vecino con items vistos. 
        # Si un usuario nuevo tiene como mejores vecinos a otros nuevos, no se recomienda nada.
        # Básicamente, añadir las preferencias en el vector del usuario solo ha servido para medir la similitud
        # entre lo vecinos con pearson, usando además de los items, las preferencias.
        for key, value in neighbor_vector.items():
            if not key.startswith("item_"):
                continue
            item_id = int(key.split("_")[1])
            if item_id in seen_items:
                continue  # No recomendar ítems ya vistos por el usuario
            if value < min_rating:
                continue  # Solo considerar ratings favorables
            if item_id not in recommendations:
                recommendations[item_id] = {'weighted_sum': 0, 'sim_sum': 0}
            recommendations[item_id]['weighted_sum'] += similarity * value
            recommendations[item_id]['sim_sum'] += abs(similarity)
    
    # Calcular la predicción final para cada ítem y sumar bonus por popularidad
    scored_items = []
    for item_id, score_data in recommendations.items():
        if score_data['sim_sum'] == 0:
            continue
        predicted_rating = score_data['weighted_sum'] / score_data['sim_sum']
        item = Item.query.get(item_id)
        if item:
            # Se añade un bonus leve por popularidad
            predicted_rating += 0.05 * item.visit_count
            scored_items.append((item, predicted_rating))
    
    if not scored_items:
        return []
    
    # Normalizar los scores a un rango de 0 a 100
    scores = [score for _, score in scored_items]
    min_score = min(scores)
    max_score = max(scores)

    if max_score > min_score:
        scored_items = [
            (item, round(((score - min_score) / (max_score - min_score)) * 100, 2))
            for item, score in scored_items
        ]
    else:
        # Si todos los scores son iguales, simplemente asignar 100 a todos o 0
        scored_items = [(item, 100) for item, score in scored_items]
    
    scored_items.sort(key=lambda x: x[1], reverse=True)
    if not all:
        return scored_items[:top_n]
    else:
        return scored_items