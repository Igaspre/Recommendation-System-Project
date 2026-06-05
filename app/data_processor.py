import os
from app import db
from app.models import User, Occupation, Preference, UserPreference, Item, ItemClassification, Rating

DATA_DIR = os.path.join(os.getcwd(), 'app', 'static', 'data')

def convert_ratio(value):
    return round(value * 100 / 7, 2)

def process_occupations():
    file_path = os.path.join(DATA_DIR, 'ocupaciones.txt')
    with open(file_path, 'r', encoding="latin-1") as f:
        lines = f.read().splitlines()
    for i in range(0, len(lines), 2):
        occ_id = int(lines[i].strip())
        occ_name = lines[i+1].strip()
        occupation = Occupation(id=occ_id, name=occ_name)
        db.session.add(occupation)
    db.session.commit()

def process_preferences():
    file_path = os.path.join(DATA_DIR, 'preferencias.txt')
    with open(file_path, 'r', encoding="latin-1") as f:
        lines = f.read().splitlines()
    for i in range(0, len(lines), 3):
        pref_id = int(lines[i].strip())
        name = lines[i+1].strip()
        parent_raw = int(lines[i+2].strip())
        parent_id = parent_raw if parent_raw != 0 else None
        pref = Preference(id=pref_id, name=name, parent_id=parent_id)
        db.session.add(pref)
    db.session.commit()

def process_users():
    file_path = os.path.join(DATA_DIR, 'usuarios_datos_personales.txt')
    with open(file_path, 'r', encoding="latin-1") as f:
        lines = f.read().splitlines()
    for i in range(0, len(lines), 8):
        user_id = int(lines[i].strip())
        username = lines[i+1].strip()
        age = int(lines[i+2].strip())
        gender = lines[i+3].strip()
        occupation_code = int(lines[i+4].strip())
        sons = int(lines[i+5].strip())
        younger_son_age = int(lines[i+6].strip())
        older_son_age = int(lines[i+7].strip())
        password = "Password123!"
        user = User(
            id=user_id,
            username=username,
            password=password,
            age=age,
            gender=gender,
            occupation=occupation_code,
            sons=sons,
            younger_son_age=younger_son_age,
            older_son_age=older_son_age
        )
        db.session.add(user)
    db.session.commit()

def process_user_preferences():
    file_path = os.path.join(DATA_DIR, 'usuarios_preferencias.txt')
    with open(file_path, 'r', encoding="latin-1") as f:
        lines = f.read().splitlines()
    for i in range(0, len(lines), 3):
        user_id = int(lines[i].strip())
        pref_id = int(lines[i+1].strip())
        interest = int(lines[i+2].strip())
        up = UserPreference(user_id=user_id, preference_id=pref_id, interest=interest)
        db.session.add(up)
    db.session.commit()

def process_items():
    file_path = os.path.join(DATA_DIR, 'items.txt')
    with open(file_path, 'r', encoding="latin-1") as f:
        lines = f.read().splitlines()
    for i in range(0, len(lines), 3):
        item_id = int(lines[i].strip())
        name = lines[i+1].strip()
        visit_count = int(lines[i+2].strip())
        item = Item(id=item_id, name=name, visit_count=visit_count)
        db.session.add(item)
    db.session.commit()

def process_item_classifications():
    file_path = os.path.join(DATA_DIR, 'clasificacion_items.txt')
    with open(file_path, 'r', encoding="latin-1") as f:
        lines = f.read().splitlines()
    for i in range(0, len(lines), 3):
        item_id = int(lines[i].strip())
        pref_id = int(lines[i+1].strip())
        adequation = int(lines[i+2].strip())
        classification = ItemClassification(item_id=item_id, preference_id=pref_id, weight=adequation)
        db.session.add(classification)
    db.session.commit()

def process_ratings(dataset_type='base'):
    filename = 'puntuaciones_usuario_base.txt' if dataset_type == 'base' else 'puntuaciones_usuario_test.txt'
    file_path = os.path.join(DATA_DIR, filename)
    with open(file_path, 'r', encoding="latin-1") as f:
        lines = f.read().splitlines()
    for i in range(0, len(lines), 3):
        user_id = int(lines[i].strip())
        item_id = int(lines[i+1].strip())
        original_rating = int(lines[i+2].strip())
        # Convertimos a 1-100
        converted_rating = convert_ratio(original_rating)
        rating = Rating(user_id=user_id, item_id=item_id, rating=converted_rating, dataset=dataset_type)
        db.session.add(rating)
    db.session.commit()

def initialize_database():
    process_occupations()
    process_preferences()
    process_users()
    process_user_preferences()
    process_items()
    process_item_classifications()
    process_ratings('base')
    process_ratings('test')
    print("Base de datos inicializada con éxito.")

if __name__ == '__main__':
    initialize_database()
