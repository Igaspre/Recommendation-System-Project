from .models import Item, User

def get_system_weight(selected_systems, system):
    """
    Determina el peso porcentual (0-100) de un sistema de recomendación en función
    de cuántos sistemas se hayan seleccionado ('SR_DE', 'SR_BC', 'SR_COL').
    """
    n_systems = len(selected_systems)
    
    if n_systems == 1:
        return 100
    elif n_systems == 2:
        return 50
    elif n_systems == 3:
        weights = {'SR_DE': 20, 'SR_BC': 40, 'SR_COL': 40}
        return weights.get(system, 33)
    else:
        return 100 / n_systems
    

def merge_individual_recommendations(recommendations_dict, selected_systems, n=10, all=False):
    """
    Fusiona las recomendaciones individuales de cada sistema aplicando su peso
    correspondiente. Devuelve una lista de tuplas (item, score) ordenada por puntuación.
    """
    rec_dict = {}
    
    # Fusionar recomendaciones con sus pesos correspondientes
    for system in selected_systems:
        if system in recommendations_dict:
            weight = get_system_weight(selected_systems, system)
            for item, ratio in recommendations_dict[system]:
                rec_dict[item.id] = round(rec_dict.get(item.id, 0) + (weight * ratio) / 100.0, 2)
                
    # Convertir el diccionario en una lista de tuplas, ordenar y tomar los n primeros
    merged_recommendations = [(Item.query.get(iid), final_ratio) for iid, final_ratio in rec_dict.items()]
    merged_recommendations.sort(key=lambda tup: tup[1], reverse=True)
    if not all:
        return merged_recommendations[:n]
    else:
        return merged_recommendations