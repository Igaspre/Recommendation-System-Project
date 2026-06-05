from .models import Item, User
from .utils import get_system_weight

def aggregate_group_recommendations(all_recommendations, selected_systems):
    """
    Técnica de agregación de recomendaciones para grupo.
    Usa el promedio de las puntuaciones para cada ítem, considerando los pesos de los sistemas.
    
    Args:
        all_recommendations: Diccionario con recomendaciones por usuario y sistema
        selected_systems: Lista de sistemas seleccionados ('SR_DE', 'SR_BC', 'SR_COL')
        
    Returns:
        list: Lista de tuplas (item, score) ordenadas por puntuación
    """
    aggregated_scores = {}
    item_counts = {}
    
    # Para cada usuario en el grupo
    for user_id, user_recommendations in all_recommendations.items():
        # Para cada sistema de recomendación seleccionado
        for system in selected_systems:
            if system in user_recommendations:
                weight = get_system_weight(selected_systems, system)
                
                # Para cada ítem recomendado para este usuario con este sistema
                for item, score in user_recommendations[system]:
                    item_id = item.id
                    if item_id not in aggregated_scores:
                        aggregated_scores[item_id] = 0
                        item_counts[item_id] = 0
                    
                    # Aplicar peso del sistema y agregar puntuación
                    aggregated_scores[item_id] += (weight * score) / 100.0
                    item_counts[item_id] += 1
    
    # Calcular puntuación final (promedio)
    final_scores = {}
    for item_id, total_score in aggregated_scores.items():
        if item_counts[item_id] > 0:
            final_scores[item_id] = total_score / len(all_recommendations)
    
    # Convertir a lista de tuplas, ordenar y limitar a 10 ítems
    merged_recommendations = [(Item.query.get(iid), score) for iid, score in final_scores.items()]
    merged_recommendations.sort(key=lambda tup: tup[1], reverse=True)
    return merged_recommendations[:10]

def calculate_group_item_ratings(all_recommendations, merged_recommendations, selected_systems):
    """
    Calcula la adecuación de cada ítem para cada usuario del grupo.
    
    Args:
        all_recommendations: Diccionario con recomendaciones por usuario y sistema
        merged_recommendations: Lista de tuplas (item, score) con las recomendaciones finales
        selected_systems: Lista de sistemas seleccionados ('SR_DE', 'SR_BC', 'SR_COL')
        
    Returns:
        dict: Diccionario con el formato {item_id: {user_id: rating}}
    """
    group_ratings = {}
    
    # Solo para los ítems que están en las recomendaciones finales
    for item, _ in merged_recommendations:
        item_id = str(item.id)
        group_ratings[item_id] = {}
        
        # Para cada usuario en el grupo
        for user_id, user_recommendations in all_recommendations.items():
            # Inicializar rating para este usuario y este ítem
            user_rating = 0
            
            # Para cada sistema, buscar si este ítem está en las recomendaciones
            for system in selected_systems:
                if system in user_recommendations:
                    weight = get_system_weight(selected_systems, system)
                    
                    # Buscar el ítem en las recomendaciones de este sistema
                    for rec_item, score in user_recommendations[system]:
                        if rec_item.id == item.id:
                            # Aplicar peso del sistema
                            user_rating += (weight * score) / 100.0
                            break
            
            # Normalizar a escala 0-100
            user_rating = min(100, max(0, user_rating))
            group_ratings[item_id][user_id] = user_rating
    
    return group_ratings

def get_group_recommendations(users, selected_systems, recommender_functions):
    """
    Obtiene recomendaciones para un grupo de usuarios.
    
    Args:
        users: Lista de objetos User del grupo
        selected_systems: Lista de sistemas seleccionados ('SR_DE', 'SR_BC', 'SR_COL')
        recommender_functions: Diccionario de funciones recomendadoras por sistema
        
    Returns:
        tuple: (recomendaciones_fusionadas, ratings_por_usuario)
    """
    all_recommendations = {}
    
    # Obtener recomendaciones para cada usuario y sistema
    for user in users:
        user_recommendations = {}
        
        for system in selected_systems:
            if system in recommender_functions:
                # Llamar a la función correspondiente para este sistema
                recs = recommender_functions[system](user)
                user_recommendations[system] = recs
        
        all_recommendations[str(user.id)] = user_recommendations
    
    # Aplicar técnica de agregación
    merged_recommendations = aggregate_group_recommendations(all_recommendations, selected_systems)
    
    # Calcular adecuación por usuario para cada ítem recomendado
    group_ratings = calculate_group_item_ratings(all_recommendations, merged_recommendations, selected_systems)
    
    return merged_recommendations, group_ratings