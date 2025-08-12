import os
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Initialiser l'application Flask
app = Flask(__name__)

# Configuration de la base de données
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///synchronie.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialiser les extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modèles de base (nous les développerons plus tard)
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    date_creation = db.Column(db.DateTime, default=db.func.current_timestamp())

class Seance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    date_seance = db.Column(db.DateTime, default=db.func.current_timestamp())
    transcription = db.Column(db.Text)
    synthese = db.Column(db.Text)

# Routes de base
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Point de contrôle pour vérifier que l'application fonctionne"""
    return jsonify({
        'status': 'healthy',
        'message': 'Synchronie API is running',
        'version': '1.0.0'
    })

@app.route('/api/patients')
def get_patients():
    """Endpoint pour récupérer la liste des patients"""
    patients = Patient.query.all()
    return jsonify([{
        'id': p.id,
        'nom': p.nom,
        'prenom': p.prenom,
        'date_creation': p.date_creation.isoformat()
    } for p in patients])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
