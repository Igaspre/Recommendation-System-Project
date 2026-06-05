import math
import statistics
from functools import lru_cache
from sqlalchemy import desc
from .models import Item, Rating, UserPreference, Preference, ItemClassification

# -----------------------------------------------------
# 1. Cache de la jerarquía de preferencias
#    Para no reconstruirla en cada llamada
# -----------------------------------------------------
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

# -----------------------------------------------------
# 2. Selección y filtrado de las preferencias del usuario
# -----------------------------------------------------
def get_content_based_preferences(user_id, top_n=20, depurate=False):
    """
    Devuelve hasta top_n preferencias del usuario, filtradas y ordenadas:
      1) Carga y ordena las preferencias por interest desc.
      2) Aplica un umbral dinámico para centrar solo en sus intereses más fuertes.
      3) Omite preferencias de nivel 1 si existen subpreferencias con interés superior.
      4) Devuelve una lista [(pref_id, interest, parent_id_or_None), ...].
    """
    # 2.1) Cargar preferencias de usuario
    user_prefs = (
        UserPreference.query
        .filter_by(user_id=user_id)
        .order_by(desc(UserPreference.interest))
        .all()
    )
    if not user_prefs:
        return []

    # 2.2) Definir umbral dinámico: interés del elemento top_n-ésimo
    threshold = user_prefs[top_n - 1].interest if len(user_prefs) >= top_n else 0

    # 2.3) Construir dict {pref_id: (interest, parent_id)} filtrado por umbral
    hierarchy = get_preference_hierarchy()
    pref_data = {
        up.preference_id: (up.interest, up.preference.parent_id)
        for up in user_prefs
        if up.interest >= threshold
    }

    # 2.4) Agrupar subpreferencias para cada padre
    parent_to_children = {}
    for pid, (interest, parent) in pref_data.items():
        parent_to_children.setdefault(parent, []).append((pid, interest))

    # 2.5) Filtrar padres vs. hijos
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

    # 2.6) Ordenar por interés descendente y limitar a top_n
    final.sort(key=lambda x: x[1], reverse=True)

    if depurate:
        print(f"User prefs: {user_prefs}")
        print(f"Threshold: {threshold}")
        print(f"User pref data: {pref_data}")
        print(f"parent_to_children: {parent_to_children}")
        print(f"final: {final}")

    return final[:top_n]

# -----------------------------------------------------
# 3. Cálculo del "ratio" y ranking de ítems
# -----------------------------------------------------
def compute_content_ratio_for_item(item, selected_prefs):
    """
    Calcula un score base para un item:
      - Multiplica el peso de cada clasificación por el interest del usuario.
      - Promedia sobre el número de clasificaciones relevantes.
      - Añade un bonus de popularidad usando logaritmo.
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
    1) Obtiene las preferencias filtradas del usuario.
    2) Excluye items ya vistos (dataset='base').
    3) Itera sobre todos los items para garantizar suficientes candidatos.
    4) Calcula el ratio, normaliza (Z-score + min-max) y ordena.
    5) Devuelve los top_n recomendaciones (o todos si all=True).
    """
    # 3.1) Selección de preferencias
    selected = get_content_based_preferences(user.id, top_prefs)
    if not selected:
        return []

    # 3.2) Ítems ya vistos
    seen = {
        r.item_id
        for r in Rating.query.filter_by(user_id=user.id, dataset='base')
    }

    # 3.3) Obtener todos los items como candidatos
    candidates = Item.query.all()

    # 3.4) Calcular scores
    scored = []
    for item in candidates:
        if item.id in seen:
            continue
        score = compute_content_ratio_for_item(item, selected)
        scored.append((item, score))
    if not scored:
        return []

    # 3.5) Normalización Z-score + min-max a [0,100]
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

    # 3.6) Ordenar y recortar resultados
    normalized.sort(key=lambda x: x[1], reverse=True)
    return normalized if all else normalized[:top_n]