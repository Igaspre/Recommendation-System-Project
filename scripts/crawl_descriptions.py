import os
import re
import wikipedia
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Item

wikipedia.set_lang("es")

db_path = os.path.join(os.getcwd(), 'instance', 'users.db')
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
session = Session()

DESCRIPTIONS_DIR = os.path.join(os.getcwd(), 'app', 'static', 'descriptions')
os.makedirs(DESCRIPTIONS_DIR, exist_ok=True)

def sanitize_filename(filename):
    """Sanitizar nombres de archivo (quitar caracteres extraños)."""
    return "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-')).rstrip().lower().replace(' ', '_')

def clean_wikipedia_summary(summary):
    summary = re.sub(r'\[.*?\]', '', summary)
    return summary.strip()

def get_wikipedia_description(query):
    try:
        page = wikipedia.page(query)
        summary = clean_wikipedia_summary(page.summary)
        if summary:
            return summary
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            if e.options:
                page = wikipedia.page(e.options[0])
                summary = clean_wikipedia_summary(page.summary)
                if summary:
                    return summary
        except Exception as e2:
            print(f"Error al procesar {query} (desambiguación fallida): {e2}")
    except wikipedia.exceptions.PageError:
        pass
    except Exception as e:
        print(f"Error al procesar {query}: {e}")

    try:
        results = wikipedia.search(query)
        if results:
            for candidate in results:
                if candidate.lower() != query.lower():
                    try:
                        page = wikipedia.page(candidate)
                        summary = clean_wikipedia_summary(page.summary)
                        if summary:
                            return summary
                    except Exception as e2:
                        print(f"Error cargando resultado '{candidate}' para {query}: {e2}")
        return None
    except Exception as e:
        print(f"Error buscando {query}: {e}")
        return None

# Obtener todos los items
items = session.query(Item).all()

NO_DESCRIPCION = "No se encontró descripción disponible en Wikipedia."

no_encontrado = []

for item in items:
    print(f"Procesando: {item.name}")
    
    description = get_wikipedia_description(item.name)
    
    if not description:
        description = NO_DESCRIPCION
        no_encontrado.append(item.name)
    
    filename_desc = sanitize_filename(item.name)
    desc_path = os.path.join(DESCRIPTIONS_DIR, f"{filename_desc}.txt")
    with open(desc_path, 'w', encoding='utf-8') as f:
        f.write(description)
    
    print(f"Descripción guardada en: {desc_path}")

print("Proceso finalizado.")
print("Items sin descripción de Wikipedia (se puso texto por defecto):")
print(no_encontrado)