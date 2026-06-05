import sys
import os
import shutil
import matplotlib.pyplot as plt
from math import fabs
from statistics import mean
from app import db, create_app 
from app.models import User, Rating
from app.demographic_recommendation import get_items_recommendation
from app.content_based_recommendation import get_content_based_recommendations
from app.collaborative_recommendation import get_collaborative_recommendations
from app.utils import merge_individual_recommendations
import json

##############################
# CONFIGURACIONES Y PARÁMETROS
##############################

# Cantidad de usuarios a evaluar
NUM_USERS = 20

# Cantidad mínima de valoraciones en test para "preferir" a un usuario.
MIN_TEST_RATINGS = 5

# Umbral para considerar un ítem "relevante"
THRESHOLD_RECOMMENDED = 45
THRESHOLD_TEST = 45

# Carpeta donde se guardarán las métricas y gráficas
METRICS_FOLDER = "metrics"

##############################
# FUNCIONES DE APOYO
##############################

def limpiar_carpeta_metrics():
    """
    Elimina todos los ficheros y subcarpetas dentro de METRICS_FOLDER
    para regenerar resultados de cero.
    """
    if os.path.exists(METRICS_FOLDER):
        for filename in os.listdir(METRICS_FOLDER):
            file_path = os.path.join(METRICS_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
            else:
                shutil.rmtree(file_path)
    else:
        os.makedirs(METRICS_FOLDER, exist_ok=True)

def obtener_top_usuarios_por_test_ratings():
    """
    Devuelve una lista de tuplas (user_id, total_score) ordenadas de mayor a menor,
    según la suma total de los ratings (score) de todos los items en el dataset 'test'.
    """
    usuarios_test = (db.session.query(Rating.user_id, db.func.sum(Rating.rating).label("total_score"))
                     .filter(Rating.dataset == 'test')
                     .group_by(Rating.user_id)
                     .order_by(db.func.sum(Rating.rating).desc())
                     .all())
    return usuarios_test

def seleccionar_usuarios_para_evaluacion():
    """
    Selecciona 20 usuarios:
      - Primero, los que tengan > MIN_TEST_RATINGS (ordenados desc).
      - Si no hay suficientes, se completa igualmente con los primeros de la lista (ordenada desc).
    """
    # Suponiendo que obtener_top_usuarios_por_test_ratings() devuelve tuplas (user_id, total_score)
    usuarios_test = obtener_top_usuarios_por_test_ratings()
    # Extraemos solo los user_ids (el primer elemento de cada tupla)
    user_ids_ordenados = [uid for uid, _ in usuarios_test]

    # Separamos los que tienen más de MIN_TEST_RATINGS
    user_ids_suficientes = []
    user_ids_restantes = []
    for uid in user_ids_ordenados:
        c = db.session.query(Rating).filter(Rating.dataset=='test', Rating.user_id==uid).count()
        if c > MIN_TEST_RATINGS:
            user_ids_suficientes.append(uid)
        else:
            user_ids_restantes.append(uid)
    
    # Tomamos primero de user_ids_suficientes hasta llegar a NUM_USERS
    seleccion = user_ids_suficientes[:NUM_USERS]
    if len(seleccion) < NUM_USERS:
        faltan = NUM_USERS - len(seleccion)
        seleccion.extend(user_ids_restantes[:faltan])
    
    return seleccion[:NUM_USERS]

def obtener_diccionario_test(usuario_id):
    """
    Devuelve dict: {item_id: rating_del_test} para dataset='test' y user_id dado.
    """
    regs = (db.session.query(Rating)
            .filter(Rating.user_id == usuario_id, Rating.dataset == 'test')
            .all())
    return {r.item_id: r.rating for r in regs}

def calcular_precision_recall_f1(set_relevantes_recomendados, set_relevantes_test):
    """
    Dado:
      - set_relevantes_recomendados: ítems que el SR consideró relevantes (>= THRESHOLD_RECOMMENDED)
      - set_relevantes_test: ítems relevantes según test (>= THRESHOLD_TEST)
    Devuelve (precision, recall, f1).
    """
    interseccion = set_relevantes_recomendados.intersection(set_relevantes_test)
    inter_count = len(interseccion)
    
    precision = 0.0
    if len(set_relevantes_recomendados) > 0:
        precision = inter_count / len(set_relevantes_recomendados)
    
    recall = 0.0
    if len(set_relevantes_test) > 0:
        recall = inter_count / len(set_relevantes_test)
    
    f1 = 0.0
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    return precision, recall, f1

def calcular_mae(dict_recomendados, dict_test):
    """
    MAE entre las predicciones (escala 0..100) y test (escala 0..100).
    Si un ítem recomendado no existe en test => se asume rating real = 0. 
    """
    if not dict_recomendados:
        return 0.0
    
    errores = []
    for item_id, rating_pred in dict_recomendados.items():
        rating_real = dict_test.get(item_id, 0.0)
        errores.append(abs(rating_pred - rating_real))
    
    return mean(errores)

def generar_grafica_lineas_por_usuario(
    eje_x_usuarios,
    valores_por_sistema,
    titulo,
    nombre_eje_y,
    nombre_fichero_salida
):
    """
    Genera y guarda en METRICS_FOLDER una gráfica de líneas donde:
      - X = listado de usuarios
      - valores_por_sistema: dict { "NombreSistema": [v1, v2, ...] }
    Se crea una línea por sistema.
    """
    plt.figure()
    for nombre_sistema, valores in valores_por_sistema.items():
        plt.plot(eje_x_usuarios, valores, marker='o', label=nombre_sistema)
    
    plt.title(titulo)
    plt.xlabel("Usuario (ID)")
    plt.ylabel(nombre_eje_y)
    plt.legend()
    plt.grid(True)
    
    ruta_salida = os.path.join(METRICS_FOLDER, nombre_fichero_salida)
    plt.savefig(ruta_salida, bbox_inches='tight')
    plt.close()

def obtener_recomendaciones_demografico(user):
    """
    SR Demográfico con n=TOP_N.
    Supone que get_items_recommendation() retorna [(item, rating), ...] con rating en [0..100].
    """
    recs = get_items_recommendation(user, all=True)
    # Escalar a 0..7
    return [(item, r) for (item, r) in recs]

def obtener_recomendaciones_contenido(user):
    """
    SR Basado en contenido con top_n=TOP_N. Retorna rating en [0..100].
    """
    recs = get_content_based_recommendations(user, all=True)
    return [(item, r) for (item, r) in recs]

def obtener_recomendaciones_colaborativo(user):
    """
    SR Colaborativo con top_n=TOP_N. Retorna rating en [0..100].
    """
    recs = get_collaborative_recommendations(user, all=True)
    return [(item, r) for (item, r) in recs]

def obtener_recomendaciones_hibrido(user):
    """
    SR Híbrido, usando merge_individual_recommendations con n=TOP_N.
    Retorna rating en [0..100].
    """
    recs_demografico = obtener_recomendaciones_demografico(user)
    recs_contenido = obtener_recomendaciones_contenido(user)
    recs_colaborativo = obtener_recomendaciones_colaborativo(user)

    # Empaquetar en dict para merge
    dict_sistemas = {
        'SR_DE': recs_demografico,
        'SR_BC': recs_contenido,
        'SR_COL': recs_colaborativo
    }
    sistemas_seleccionados = ['SR_DE', 'SR_BC', 'SR_COL']
    # merge_individual_recommendations(dict_sistemas, selected_systems, n=TOP_N)
    merged = merge_individual_recommendations(dict_sistemas, sistemas_seleccionados, all=True)
    merged_escala = []
    for (item, r) in merged:
        merged_escala.append((item, r))
    return merged_escala

def evaluar_sistemas_recomendacion():
    """
    Función principal que:
      - Limpia carpeta metrics/
      - Selecciona 20 usuarios
      - Para cada usuario, obtiene recomendaciones de SR demográfico, contenido, colaborativo, híbrido
      - Calcula precisión, recall, F1, MAE
      - Genera gráficas
      - Guarda en un txt los valores promediados y por usuario
    """
    # Crear la app Flask si usas create_app(), o ajusta a tu forma de inicializar
    app = create_app()
    with app.app_context():
        # 1) Limpiar carpeta metrics
        limpiar_carpeta_metrics()

        # 2) Seleccionar usuarios
        usuarios = seleccionar_usuarios_para_evaluacion()
        print(f"Usuarios seleccionados para evaluación: {usuarios}")

        # Listas donde guardaremos métricas por usuario y sistema
        precision_DE, recall_DE, f1_DE, mae_DE = [], [], [], []
        precision_BC, recall_BC, f1_BC, mae_BC = [], [], [], []
        precision_COL, recall_COL, f1_COL, mae_COL = [], [], [], []
        precision_HIB, recall_HIB, f1_HIB, mae_HIB = [], [], [], []

        datos_evaluacion = []

        # 3) Calcular métricas
        for idx, user_id in enumerate(usuarios):
            user = db.session.get(User, user_id)
            if not user:
                continue

            # Dic. test
            dict_test = obtener_diccionario_test(user_id)

            # Recomendaciones SR Demográfico
            recs_de = obtener_recomendaciones_demografico(user)
            dict_de = {item.id: rating for (item, rating) in recs_de}

            # Recomendaciones SR Contenido
            recs_bc = obtener_recomendaciones_contenido(user)
            dict_bc = {item.id: rating for (item, rating) in recs_bc}

            # Recomendaciones SR Colaborativo
            recs_col = obtener_recomendaciones_colaborativo(user)
            dict_col = {item.id: rating for (item, rating) in recs_col}

            # Recomendaciones SR Híbrido
            recs_hib = obtener_recomendaciones_hibrido(user)
            dict_hib = {item.id: rating for (item, rating) in recs_hib}

            # Relevantes recomendados
            rel_de = {i for i, r in dict_de.items() if r >= THRESHOLD_RECOMMENDED}
            rel_bc = {i for i, r in dict_bc.items() if r >= THRESHOLD_RECOMMENDED}
            rel_col= {i for i, r in dict_col.items() if r >= THRESHOLD_RECOMMENDED}
            rel_hib= {i for i, r in dict_hib.items() if r >= THRESHOLD_RECOMMENDED}

            # Relevantes test
            rel_test = {i for i, r in dict_test.items() if r >= THRESHOLD_TEST}

            # Prec/Recall/F1
            p_de, r_de, f1_de = calcular_precision_recall_f1(rel_de, rel_test)
            p_bc, r_bc, f1_bc = calcular_precision_recall_f1(rel_bc, rel_test)
            p_col, r_col, f1_col = calcular_precision_recall_f1(rel_col, rel_test)
            p_hib, r_hib, f1_hib = calcular_precision_recall_f1(rel_hib, rel_test)

            precision_DE.append(p_de)
            recall_DE.append(r_de)
            f1_DE.append(f1_de)

            precision_BC.append(p_bc)
            recall_BC.append(r_bc)
            f1_BC.append(f1_bc)

            precision_COL.append(p_col)
            recall_COL.append(r_col)
            f1_COL.append(f1_col)

            precision_HIB.append(p_hib)
            recall_HIB.append(r_hib)
            f1_HIB.append(f1_hib)

            # MAE
            mae_DE.append(calcular_mae(dict_de, dict_test))
            mae_BC.append(calcular_mae(dict_bc, dict_test))
            mae_COL.append(calcular_mae(dict_col, dict_test))
            mae_HIB.append(calcular_mae(dict_hib, dict_test))

            # Almacena los datos del usuario en un diccionario
            datos_usuario = {
                "user_id": user_id,
                "dict_test": dict_test,
                "recs_demografico": dict_de,
                "recs_contenido": dict_bc,
                "recs_colaborativo": dict_col,
                "recs_hibrido": dict_hib
            }
            
            # Añade el diccionario a la lista global
            datos_evaluacion.append(datos_usuario)
        
        # Define la ruta del fichero a exportar
        ruta_json = os.path.join(METRICS_FOLDER, "datos_evaluacion.json")
        with open(ruta_json, "w", encoding="utf-8") as archivo:
            json.dump(datos_evaluacion, archivo, ensure_ascii=False, indent=4)

        # 4) Gráficas

        # Reordenamos la lista de usuarios de menor a mayor
        usuarios_ordenados = sorted(usuarios)

        # Reordenamos las métricas según el orden ascendente de los IDs
        precision_DE_sorted = [precision_DE[usuarios.index(u)] for u in usuarios_ordenados]
        recall_DE_sorted    = [recall_DE[usuarios.index(u)] for u in usuarios_ordenados]
        f1_DE_sorted        = [f1_DE[usuarios.index(u)] for u in usuarios_ordenados]
        mae_DE_sorted       = [mae_DE[usuarios.index(u)] for u in usuarios_ordenados]

        precision_BC_sorted = [precision_BC[usuarios.index(u)] for u in usuarios_ordenados]
        recall_BC_sorted    = [recall_BC[usuarios.index(u)] for u in usuarios_ordenados]
        f1_BC_sorted        = [f1_BC[usuarios.index(u)] for u in usuarios_ordenados]
        mae_BC_sorted       = [mae_BC[usuarios.index(u)] for u in usuarios_ordenados]

        precision_COL_sorted = [precision_COL[usuarios.index(u)] for u in usuarios_ordenados]
        recall_COL_sorted    = [recall_COL[usuarios.index(u)] for u in usuarios_ordenados]
        f1_COL_sorted        = [f1_COL[usuarios.index(u)] for u in usuarios_ordenados]
        mae_COL_sorted       = [mae_COL[usuarios.index(u)] for u in usuarios_ordenados]

        precision_HIB_sorted = [precision_HIB[usuarios.index(u)] for u in usuarios_ordenados]
        recall_HIB_sorted    = [recall_HIB[usuarios.index(u)] for u in usuarios_ordenados]
        f1_HIB_sorted        = [f1_HIB[usuarios.index(u)] for u in usuarios_ordenados]
        mae_HIB_sorted       = [mae_HIB[usuarios.index(u)] for u in usuarios_ordenados]

        # Generamos gráficas para cada sistema usando la lista ordenada de usuarios

        # Demográfico
        generar_grafica_lineas_por_usuario(
            usuarios_ordenados,
            {"Precisión": precision_DE_sorted, "Recall": recall_DE_sorted, "F1": f1_DE_sorted},
            "SR Demográfico: Precisión, Recall, F1",
            "Valor",
            "SR_DE_pr_re_f1.png"
        )
        generar_grafica_lineas_por_usuario(
            usuarios_ordenados,
            {"MAE": mae_DE_sorted},
            "SR Demográfico: MAE",
            "MAE",
            "SR_DE_mae.png"
        )

        # Basado en Contenido
        generar_grafica_lineas_por_usuario(
            usuarios_ordenados,
            {"Precisión": precision_BC_sorted, "Recall": recall_BC_sorted, "F1": f1_BC_sorted},
            "SR Contenido: Precisión, Recall, F1",
            "Valor",
            "SR_BC_pr_re_f1.png"
        )
        generar_grafica_lineas_por_usuario(
            usuarios_ordenados,
            {"MAE": mae_BC_sorted},
            "SR Contenido: MAE",
            "MAE",
            "SR_BC_mae.png"
        )

        # Colaborativo
        generar_grafica_lineas_por_usuario(
            usuarios_ordenados,
            {"Precisión": precision_COL_sorted, "Recall": recall_COL_sorted, "F1": f1_COL_sorted},
            "SR Colaborativo: Precisión, Recall, F1",
            "Valor",
            "SR_COL_pr_re_f1.png"
        )
        generar_grafica_lineas_por_usuario(
            usuarios_ordenados,
            {"MAE": mae_COL_sorted},
            "SR Colaborativo: MAE",
            "MAE",
            "SR_COL_mae.png"
        )

        # Híbrido
        generar_grafica_lineas_por_usuario(
            usuarios_ordenados,
            {"Precisión": precision_HIB_sorted, "Recall": recall_HIB_sorted, "F1": f1_HIB_sorted},
            "SR Híbrido: Precisión, Recall, F1",
            "Valor",
            "SR_HIB_pr_re_f1.png"
        )
        generar_grafica_lineas_por_usuario(
            usuarios_ordenados,
            {"MAE": mae_HIB_sorted},
            "SR Híbrido: MAE",
            "MAE",
            "SR_HIB_mae.png"
        )


        # 5) Guardar resultados en un TXT
        ruta_txt = os.path.join(METRICS_FOLDER, "evaluation_results.txt")
        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write("Resultados de Evaluación de SR\n")
            f.write("Usuarios evaluados: {}\n\n".format(usuarios))

            def stats_str(label, prec, rec, f1, mae):
                return (
                    f"{label} => "
                    f"Precisión promedio: {mean(prec):.4f}, "
                    f"Recall promedio: {mean(rec):.4f}, "
                    f"F1 promedio: {mean(f1):.4f}, "
                    f"MAE promedio: {mean(mae):.4f}"
                )

            f.write(stats_str("SR Demográfico", precision_DE, recall_DE, f1_DE, mae_DE) + "\n")
            f.write(stats_str("SR Contenido", precision_BC, recall_BC, f1_BC, mae_BC) + "\n")
            f.write(stats_str("SR Colaborativo", precision_COL, recall_COL, f1_COL, mae_COL) + "\n")
            f.write(stats_str("SR Híbrido", precision_HIB, recall_HIB, f1_HIB, mae_HIB) + "\n")
            
            f.write("\n--- Datos por usuario ---\n")
            for i, uid in enumerate(usuarios):
                f.write(f"\nUsuario ID: {uid}\n")
                f.write(f"  SR_DE => Prec: {precision_DE[i]:.4f}, Rec: {recall_DE[i]:.4f}, F1: {f1_DE[i]:.4f}, MAE: {mae_DE[i]:.4f}\n")
                f.write(f"  SR_BC => Prec: {precision_BC[i]:.4f}, Rec: {recall_BC[i]:.4f}, F1: {f1_BC[i]:.4f}, MAE: {mae_BC[i]:.4f}\n")
                f.write(f"  SR_COL => Prec: {precision_COL[i]:.4f}, Rec: {recall_COL[i]:.4f}, F1: {f1_COL[i]:.4f}, MAE: {mae_COL[i]:.4f}\n")
                f.write(f"  SR_HIB => Prec: {precision_HIB[i]:.4f}, Rec: {recall_HIB[i]:.4f}, F1: {f1_HIB[i]:.4f}, MAE: {mae_HIB[i]:.4f}\n")

        print(f"\n¡Evaluación completada! Resultados y gráficas en la carpeta '{METRICS_FOLDER}'.")


if __name__ == "__main__":
    evaluar_sistemas_recomendacion()