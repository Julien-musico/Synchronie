"""
Routes principales de l'application
"""
from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@main.route('/dashboard')
def dashboard():
    """Tableau de bord principal"""
    return render_template('dashboard.html')
