from flask import render_template, request, redirect, url_for, session
from flask import Flask
from flask import jsonify
import os
from . import db
from .models import User, Item, UserPreference, Occupation, Preference, Favorite, Rating
from . import app
from .data_processor import initialize_database
from sqlalchemy import func, or_
from .demographic_recommendation import get_items_recommendation
from .content_based_recommendation import get_content_based_recommendations
from .collaborative_recommendation import get_collaborative_recommendations
from .group_recommendation import get_group_recommendations
from .utils import merge_individual_recommendations

# Ruta principal
@app.route('/')
def home():
    if any(db.session.query(func.count()).select_from(table).scalar() > 0 for table in db.metadata.sorted_tables):
        return render_template('index.html')

    initialize_database()
    return render_template('index.html')

@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        return dict(logged_in_user=user)
    return dict(logged_in_user=None)

# Registro de usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="El usuario ya existe.")
        
        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char in '!@#$%^&*()_+' for char in password):
            return render_template('register.html', error="La contraseña debe tener al menos 8 caracteres, un número y un carácter especial.")
        
        age = int(request.form['age'])
        gender = request.form['gender']
        occupation_id = request.form['occupation']
        sons = int(request.form['sons'])
        younger_son_age = int(request.form.get('younger_son_age', 0))
        older_son_age = int(request.form.get('older_son_age',0))
        
        # Crear el nuevo usuario
        new_user = User(
            username=username,
            password=password,
            age=age,
            gender=gender,
            occupation=int(occupation_id),
            sons=sons,
            younger_son_age=younger_son_age,
            older_son_age=older_son_age
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Procesar las preferencias seleccionadas
        pref_ids = request.form.getlist('preferences')
        for pid in pref_ids:
            # Añadimos un valor por defecto de 5 si no se especifica
            interest_val = request.form.get('interest_' + pid, 5)
            up = UserPreference(user_id=new_user.id, preference_id=int(pid), interest=int(interest_val))
            db.session.add(up)
        db.session.commit()
        
        # Iniciar sesión automáticamente asignando el ID del usuario a la sesión
        session['user_id'] = new_user.id
        return redirect(url_for('dashboard'))
    
    # En el GET, se consulta la lista de ocupaciones y de preferencias para mostrar en el formulario
    occupations = Occupation.query.all()
    preferences = Preference.query.all()
    return render_template('register.html', occupations=occupations, preferences=preferences)

# Inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if user.password == password:
                session['user_id'] = user.id
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Contraseña incorrecta.")
        else:
            return render_template('login.html', error="Usuario no encontrado.")
    
    return render_template('login.html')

# Panel de usuario
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    items = Item.query.all()
    user_favorites = Favorite.query.filter_by(user_id=user.id).all()
    favorite_ids = [fav.item_id for fav in user_favorites]
    return render_template('dashboard.html', user=user, items=items, favorite_ids=favorite_ids)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))

    occupations = Occupation.query.all()
    preferences = Preference.query.all()
    
    if request.method == 'POST':
        # Tomar todos los campos del formulario
        form_username = request.form['username']
        form_password = request.form['password']
        form_age = request.form['age']
        form_gender = request.form['gender']
        form_occupation = request.form['occupation']
        form_sons = request.form['sons']
        form_younger_son_age = request.form['younger_son_age']
        form_older_son_age = request.form['older_son_age']
        
        # Validar la contraseña antes de actualizar la BD
        if len(form_password) < 8 or not any(char.isdigit() for char in form_password) or not any(char in '!@#$%^&*()_+' for char in form_password):
            # Construir un mapa temporal de preferencias para que el template sepa cuáles se habían marcado
            temp_pref_map = {}
            # Prefs seleccionadas
            pref_ids = request.form.getlist('preferences')
            for pid in pref_ids:
                interest_val = request.form.get('interest_' + pid, 5)
                temp_pref_map[int(pid)] = int(interest_val)
            
            # Devolver la plantilla con los datos que el usuario escribió
            return render_template(
                'profile.html', 
                user=user,
                occupations=occupations,
                preferences=preferences,
                error="La contraseña debe tener al menos 8 caracteres, un número y un carácter especial.",
                
                # Pasamos los valores del formulario para rellenarlos en la plantilla:
                form_username=form_username,
                form_password=form_password,
                form_age=form_age,
                form_gender=form_gender,
                form_occupation=form_occupation,
                form_sons=form_sons,
                form_younger_son_age=form_younger_son_age,
                form_older_son_age=form_older_son_age,
                
                # Mapa de preferencias temporal (checkboxes e intereses)
                temp_pref_map=temp_pref_map
            )

        # Si la contraseña es válida, entonces ya sí actualizamos definitivamente
        user.username = form_username
        user.password = form_password
        user.age = int(form_age)
        user.gender = form_gender
        user.occupation = int(form_occupation)
        user.sons = int(form_sons)
        user.younger_son_age = int(form_younger_son_age)
        user.older_son_age = int(form_older_son_age)
        
        # Borrar preferencias anteriores
        UserPreference.query.filter_by(user_id=user.id).delete()

        # Guardar nuevas
        pref_ids = request.form.getlist('preferences')
        for pid in pref_ids:
            interest_val = request.form.get('interest_' + pid, 5)
            up = UserPreference(
                user_id=user.id, 
                preference_id=int(pid), 
                interest=int(interest_val)
            )
            db.session.add(up)

        # Guardar en BD
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('profile.html', user=user, occupations=occupations, preferences=preferences)

# Para las descripciones de los sitios
@app.route('/item_details/<int:item_id>')
def item_details(item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    item = Item.query.get_or_404(item_id)    
    
    filename = item.name.lower().replace('(', '').replace(')', '').replace("'", '').replace(' ', '_')
    
    try:
        with open(os.path.join(app.static_folder, 'descriptions', f'{filename}.txt'), 'r', encoding='utf-8') as f:
            description = f.read().strip()
    except FileNotFoundError:
        description = "No hay descripción disponible para este destino."
    
    image_filename = item.name.replace('(', '').replace(')', '').replace("'", '') + '.png'
    
    return jsonify({
        'id': item.id,
        'name': item.name,
        'description': description,
        'image': image_filename,
        'visit_count': item.visit_count
    })

@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    if 'user_id' not in session:
        return jsonify({'error': 'No estás autenticado.'}), 401
    
    user_id = session['user_id']
    item_id = request.form.get('item_id')
    if not item_id:
        return jsonify({'error': 'Falta item_id'}), 400

    fav_existente = Favorite.query.filter_by(user_id=user_id, item_id=item_id).first()
    if fav_existente:
        return jsonify({'message': 'El item ya estaba en favoritos'}), 200

    nuevo_fav = Favorite(user_id=user_id, item_id=item_id)
    db.session.add(nuevo_fav)
    db.session.commit()
    return jsonify({'message': 'Favorito guardado con éxito'}), 200


@app.route('/remove_favorite', methods=['POST'])
def remove_favorite():
    if 'user_id' not in session:
        return jsonify({'error': 'No estás autenticado.'}), 401
    
    user_id = session['user_id']
    item_id = request.form.get('item_id')
    if not item_id:
        return jsonify({'error': 'Falta item_id'}), 400

    fav = Favorite.query.filter_by(user_id=user_id, item_id=item_id).first()
    if not fav:
        return jsonify({'error': 'No existe ese favorito'}), 404
    
    db.session.delete(fav)
    db.session.commit()
    return jsonify({'message': 'Favorito eliminado con éxito'}), 200

@app.route('/get_users')
def get_users():
    """Obtiene la lista de usuarios para la recomendación grupal"""
    if 'user_id' not in session:
        return jsonify({'error': 'No session active'}), 401
    
    # Obtener todos los usuarios excepto el actual
    users = User.query.all()
    users_list = [{'id': str(user.id), 'username': user.username} for user in users]
    
    return jsonify({
        'users': users_list, 
        'current_user_id': str(session['user_id'])
    })

@app.route('/dashboard_ajax')
def dashboard_ajax():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    selected_systems = request.args.getlist('recommender')
    
    # Verificar si es recomendación grupal
    is_group_recommendation = request.args.get('group_recommendation') == 'true'
    group_users_ids = request.args.getlist('group_users')
    
    # Si no se ha seleccionado ningún sistema, se muestran todos los ítems.
    if not selected_systems:
        items = Item.query.all()
        favorite_ids = get_user_favorites(user.id)
        return jsonify({
            'html': render_template('_items.html', items=items, favorite_ids=favorite_ids)
        })
    
    # Definir las funciones para cada sistema de recomendación con sus parámetros
    recommender_functions = {
        'SR_DE': lambda user: get_items_recommendation(user, n=10),
        'SR_BC': lambda user: get_content_based_recommendations(user, top_n=10, top_prefs=20),
        'SR_COL': lambda user: get_collaborative_recommendations(user, top_n=10)
    }
    
    if is_group_recommendation and group_users_ids:
        # Obtener el grupo de usuarios (incluyendo el usuario actual)
        group_users = [user]  # Añadir el usuario actual al grupo
        for user_id in group_users_ids:
            group_user = User.query.get(user_id)
            if group_user and group_user.id != user.id:  # Evitar duplicados
                group_users.append(group_user)
        
        # Obtener recomendaciones para el grupo
        merged_recommendations, group_ratings = get_group_recommendations(
            group_users, 
            selected_systems, 
            recommender_functions
        )
        
        items = [item for (item, final_ratio) in merged_recommendations]
        favorite_ids = get_user_favorites(user.id)
        
        return jsonify({
            'html': render_template('_items.html', items=items, favorite_ids=favorite_ids),
            'group_ratings': group_ratings
        })
    else:
        # Recomendaciones individuales
        user_recommendations = {}
        
        # Obtener recomendaciones de cada sistema seleccionado
        for system in selected_systems:
            if system in recommender_functions:
                user_recommendations[system] = recommender_functions[system](user)
        
        # Fusionar recomendaciones individuales
        merged_recommendations = merge_individual_recommendations(user_recommendations, selected_systems)
        
        items = [item for (item, final_ratio) in merged_recommendations]
        favorite_ids = get_user_favorites(user.id)
        
        return jsonify({
            'html': render_template('_items.html', items=items, favorite_ids=favorite_ids)
        })

def get_user_favorites(user_id):
    """Devuelve los ids de los ítems marcados como favoritos por el usuario"""
    user_favorites = Favorite.query.filter_by(user_id=user_id).all()
    return [fav.item_id for fav in user_favorites]

@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    from .models import Favorite, Item
    favoritos = Favorite.query.filter_by(user_id=user_id).all()
    item_ids = [f.item_id for f in favoritos]
    
    items_favoritos = Item.query.filter(Item.id.in_(item_ids)).all()
    return render_template('favorites.html', items=items_favoritos)

@app.route('/get_rating/<int:item_id>')
def get_rating(item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user_id = session['user_id']
    rating = Rating.query.filter_by(user_id=user_id, item_id=item_id, dataset='base').first()
    if rating:
        return jsonify({'rating': rating.rating})
    else:
        return jsonify({'rating': None})

@app.route('/update_rating', methods=['POST'])
def update_rating():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user_id = session['user_id']
    item_id = request.form.get('item_id')
    rating_val = request.form.get('rating')
    if not item_id or rating_val is None:
        return jsonify({'error': 'Falta item_id o rating'}), 400
    try:
        rating_val = float(rating_val)
    except ValueError:
        return jsonify({'error': 'El rating debe ser un número'}), 400
    
    # Buscar si ya existe un rating para este usuario e ítem
    rating_record = Rating.query.filter_by(user_id=user_id, item_id=item_id, dataset='base').first()
    if rating_record:
        rating_record.rating = rating_val
        new_rating = False
    else:
        rating_record = Rating(user_id=user_id, item_id=item_id, rating=rating_val, dataset='base')
        db.session.add(rating_record)
        new_rating = True

    # Solo incrementar el contador de visitas si es un rating nuevo
    item = Item.query.get(item_id)
    if item and new_rating:
        item.visit_count += 1

    db.session.commit()
    return jsonify({'message': 'Rating actualizado', 'rating': rating_val, 'visit_count': item.visit_count if item else None})

@app.route('/delete_rating', methods=['POST'])
def delete_rating():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user_id = session['user_id']
    item_id = request.form.get('item_id')
    if not item_id:
        return jsonify({'error': 'Falta item_id'}), 400
    rating_record = Rating.query.filter_by(user_id=user_id, item_id=item_id, dataset='base').first()
    if not rating_record:
        return jsonify({'error': 'No existe rating para este ítem'}), 404
    db.session.delete(rating_record)
    # Decrementar el contador de visitas si es mayor que 0
    item = Item.query.get(item_id)
    if item and item.visit_count > 0:
        item.visit_count -= 1
    db.session.commit()
    return jsonify({'message': 'Rating eliminado', 'visit_count': item.visit_count if item else None})

# Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))