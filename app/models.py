from . import db

# Modelo intermedio para la relación entre usuarios y preferencias con un valor de interés
class UserPreference(db.Model):
    __tablename__ = 'user_preference'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    preference_id = db.Column(db.Integer, db.ForeignKey('preference.id'), primary_key=True)
    interest = db.Column(db.Integer, nullable=False)
    user = db.relationship("User", back_populates="user_preferences")
    preference = db.relationship("Preference", back_populates="user_preferences")

class Occupation(db.Model):
    __tablename__ = 'occupation'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Preference(db.Model):
    __tablename__ = 'preference'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # Si parent_id es 0 en el fichero se considera preferencia de primer nivel (sin padre)
    parent_id = db.Column(db.Integer, db.ForeignKey('preference.id'), nullable=True)
    children = db.relationship('Preference', backref=db.backref('parent', remote_side=[id]))
    # Relación con usuarios (con valor de interés)
    user_preferences = db.relationship('UserPreference', back_populates='preference')

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(1))
    # Se almacena el código de ocupación
    occupation = db.Column(db.Integer, db.ForeignKey('occupation.id'))
    sons = db.Column(db.Integer)
    younger_son_age = db.Column(db.Integer)
    older_son_age = db.Column(db.Integer)
    # Relación con preferencias a través del modelo intermedio
    user_preferences = db.relationship('UserPreference', back_populates='user')

class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    visit_count = db.Column(db.Integer, default=0)
    # Relación con clasificaciones (un ítem puede tener varias)
    classifications = db.relationship('ItemClassification', back_populates='item')

class ItemClassification(db.Model):
    __tablename__ = 'item_classification'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    preference_id = db.Column(db.Integer, db.ForeignKey('preference.id'))
    # Adecuación del ítem a la categoría (por ejemplo, 70, 20, 60, etc.)
    weight = db.Column(db.Integer)
    item = db.relationship('Item', back_populates='classifications')
    preference = db.relationship('Preference')

class Rating(db.Model):
    __tablename__ = 'rating'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    rating = db.Column(db.Integer)
    # Indica si la puntuación proviene del dataset "base" o "test"
    dataset = db.Column(db.String(10))

class Favorite(db.Model):
    __tablename__ = 'favorite'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

    user = db.relationship('User', backref='favorites')
    item = db.relationship('Item', backref='favorited_by')