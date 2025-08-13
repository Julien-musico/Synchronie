"""Routes d'authentification basiques (login / logout / register)."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required  # type: ignore
from app.models import db, User

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])  # type: ignore
def login():  # type: ignore
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Email et mot de passe requis', 'error')
                return render_template('auth/login.html')
            
            user = User.query.filter_by(email=email, actif=True).first()  # type: ignore
            if user and user.check_password(password):  # type: ignore
                login_user(user)  # type: ignore
                flash('Connexion réussie', 'success')
                next_url = request.args.get('next') or url_for('main.index')
                return redirect(next_url)
            flash('Identifiants invalides', 'error')
        except Exception as e:
            print(f"Erreur lors de la connexion: {e}")
            flash('Erreur de connexion. Veuillez réessayer.', 'error')
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])  # type: ignore
def register():  # type: ignore
    """Page d'inscription pour nouveaux musicothérapeutes."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        nom = request.form.get('nom', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Validations
        if not email or not nom or not password:
            flash('Tous les champs sont obligatoires', 'error')
            return render_template('auth/register.html')
        
        if password != password_confirm:
            flash('Les mots de passe ne correspondent pas', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères', 'error')
            return render_template('auth/register.html')
        
        # Vérifier si l'email existe déjà
        if User.query.filter_by(email=email).first():  # type: ignore
            flash('Un compte avec cet email existe déjà', 'error')
            return render_template('auth/register.html')
        
        # Créer le nouvel utilisateur
        try:
            user = User(email=email, nom=nom)  # type: ignore
            user.set_password(password)  # type: ignore
            db.session.add(user)
            db.session.commit()
            
            # Connecter automatiquement l'utilisateur
            login_user(user)  # type: ignore
            flash('Compte créé avec succès ! Bienvenue sur Synchronie', 'success')
            return redirect(url_for('main.index'))
            
        except Exception:
            db.session.rollback()
            flash('Erreur lors de la création du compte', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth.route('/logout')  # type: ignore
@login_required  # type: ignore
def logout():  # type: ignore
    logout_user()  # type: ignore
    flash('Déconnecté', 'info')
    return redirect(url_for('auth.login'))

@auth.cli.command('create-user')  # type: ignore
def create_user():  # type: ignore
    """Créer un utilisateur en ligne de commande."""
    import getpass
    email = input('Email: ').strip().lower()
    if User.query.filter_by(email=email).first():  # type: ignore
        print('Utilisateur déjà existant')
        return
    nom = input('Nom: ').strip()
    pwd = getpass.getpass('Mot de passe: ')
    user = User(email=email, nom=nom)  # type: ignore
    user.set_password(pwd)  # type: ignore
    db.session.add(user)
    db.session.commit()
    print('Utilisateur créé.')
