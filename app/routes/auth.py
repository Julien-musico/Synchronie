"""Routes d'authentification basiques (login / logout)."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required  # type: ignore
from app.models import db, User

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])  # type: ignore
def login():  # type: ignore
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, actif=True).first()  # type: ignore
        if user and user.check_password(password):  # type: ignore
            login_user(user)  # type: ignore
            flash('Connexion réussie', 'success')
            next_url = request.args.get('next') or url_for('main.index')
            return redirect(next_url)
        flash('Identifiants invalides', 'error')
    return render_template('auth/login.html')

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
