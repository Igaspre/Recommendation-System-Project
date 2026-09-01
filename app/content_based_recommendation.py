import math
import statistics
from functools import lru_cache
from sqlalchemy import desc
from .models import Item, Rating, UserPreference, Preference, ItemClassification

# Cacheamos la jerarquía de preferencias para no reconstruirla en cada llamada
@lru_cache(maxsize=1)
def get_preference_hierarchy():
    """
    Consulta todas las preferencias y construye un diccionario
    parent_id -> [child_id, ...].
    """
    all_prefs = Preference.query.all()
    hierarchy = {}
    for pref in all_prefs:
        parent = pref.parent_id
        if parent is not None:
            hierarchy.setdefault(parent, []).append(pref.id)
    return hierarchy


def has_subpreferences(pref_id, hierarchy):
    """
    Indica si una preferencia de nivel 1 tiene hijos en la jerarquía.
    """
    return pref_id in hierarchy and bool(hierarchy[pref_id])

def get_content_based_preferences(user_id, top_n=20, depurate=False):
    """
    Devuelve hasta top_n preferencias del usuario, filtradas y ordenadas por interés.
    Se aplica un umbral dinámico para quedarse solo con los intereses más fuertes y
    se omiten las preferencias de nivel 1 cuando alguna de sus subpreferencias tiene
    más interés. El resultado es una lista [(pref_id, interest, parent_id_or_None), ...].
    """
    user_prefs = (
        UserPreference.query
        .filter_by(user_id=user_id)
        .order_by(desc(UserPreference.interest))
        .all()
    )
    if not user_prefs:
        return []

    # Umbral dinámico: el interés del elemento top_n-ésimo
    threshold = user_prefs[top_n - 1].interest if len(user_prefs) >= top_n else 0

    # Dict {pref_id: (interest, parent_id)} filtrado por umbral
    hierarchy = get_preference_hierarchy()
    pref_data = {
        up.preference_id: (up.interest, up.preference.parent_id)
        for up in user_prefs
        if up.interest >= threshold
    }

    # Agrupar las subpreferencias de cada padre
    parent_to_children = {}
    for pid, (interest, parent) in pref_data.items():
        parent_to_children.setdefault(parent, []).append((pid, interest))

    # Filtrar padres frente a hijos
    final = []
    for pid, (interest, parent) in pref_data.items():
        if parent is None and has_subpreferences(pid, hierarchy):
            # Caso: preferencia de nivel 1 con hijos
            children = parent_to_children.get(pid, [])
            if children:
                max_child_interest = max(child_interest for _, child_interest in children)
                # Mantener el padre solo si es >= máximo interés de sus hijos
                if interest >= max_child_interest:
                    final.append((pid, interest, None))
            else:
                # Padre sin hijos puntuados
                final.append((pid, interest, None))
        else:
            # Subpreferencia o preferencia de nivel 1 sin hijos en la taxonomía
            final.append((pid, interest, parent))

    # Ordenar por interés descendente y limitar a top_n
    final.sort(key=lambda x: x[1], reverse=True)

    if depurate:
        print(f"User prefs: {user_prefs}")
        print(f"Threshold: {threshold}")
        print(f"User pref data: {pref_data}")
        print(f"parent_to_children: {parent_to_children}")
        print(f"final: {final}")

    return final[:top_n]

def compute_content_ratio_for_item(item, selected_prefs):
    """
    Calcula el score base de un ítem multiplicando el peso de cada clasificación por
    el interés del usuario, promediando sobre las clasificaciones relevantes y
    sumando un bonus de popularidad logarítmico.
    """
    if not selected_prefs:
        return 0

    sp_dict = {pid: interest for pid, interest, _ in selected_prefs}
    total, count = 0.0, 0

    for classif in item.classifications:
        interest = sp_dict.get(classif.preference_id)
        if interest:
            total += classif.weight * interest
            count += 1

    if count == 0:
        return 0

    ratio = total / count
    # Bonus de popularidad atenuado (logarítmico)
    ratio += 0.05 * math.log1p(item.visit_count)
    return ratio


def get_content_based_recommendations(user, top_n=10, top_prefs=20, all=False):
    """
    Recomienda ítems a partir de las preferencias filtradas del usuario, excluyendo
    los que ya ha visto (dataset='base'). Recorre todos los ítems para tener candidatos
    suficientes, calcula el ratio, lo normaliza (Z-score + min-max) y ordena.
    Devuelve las top_n recomendaciones, o todas si all=True.
    """
    selected = get_content_based_preferences(user.id, top_prefs)
    if not selected:
        return []

    # Ítems ya vistos
    seen = {
        r.item_id
        for r in Rating.query.filter_by(user_id=user.id, dataset='base')
    }

    # Todos los ítems son candidatos
    candidates = Item.query.all()

    scored = []
    for item in candidates:
        if item.id in seen:
            continue
        score = compute_content_ratio_for_item(item, selected)
        scored.append((item, score))
    if not scored:
        return []

    # Normalización Z-score + min-max a [0,100]
    ratios = [score for _, score in scored]
    mean = statistics.mean(ratios)
    stdev = statistics.pstdev(ratios) or 1.0
    zscores = [(item, (score - mean) / stdev) for item, score in scored]

    zs = [z for _, z in zscores]
    min_z, max_z = min(zs), max(zs)
    normalized = []
    for item, z in zscores:
        if max_z > min_z:
            norm = (z - min_z) / (max_z - min_z) * 100
        else:
            norm = 50.0
        normalized.append((item, round(norm, 2)))

    # Ordenar y recortar resultados
    normalized.sort(key=lambda x: x[1], reverse=True)
    return normalized if all else normalized[:top_n]