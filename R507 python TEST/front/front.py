from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

# URL du service API
api_service_url = 'http://api_back:5000'
@app.route('/')
def accueil():
    try:
        response = requests.get(api_service_url)
        response.raise_for_status()
        message = response.json().get('message', 'Bienvenue sur l’interface utilisateur.')
        return render_template('index.jinja2', message=message)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('index.jinja2', error=str(e))

@app.route('/utilisateurs')
def utilisateurs():
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.get(f"{api_service_url}/utilisateurs", headers=headers)
        response.raise_for_status()
        utilisateurs = response.json()
        nom_colonne = ["ID", "Nom", "Email", "Nombre de livres empruntés"]
        return render_template('utilisateurs.jinja2', utilisateurs=utilisateurs, col=nom_colonne)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('utilisateurs.jinja2', error=str(e))

@app.route('/livres')
def livres():
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.get(f"{api_service_url}/livres", headers=headers)
        response.raise_for_status()
        lst_livres = response.json()
        nom_colonne = ["ID", "Titre", "Résumé", "Date de publication", "Auteur", "Disponibilité"]
        return render_template('livres.jinja2', lst=lst_livres, col=nom_colonne)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('livres.jinja2', error=str(e))

@app.route('/auteurs')
def auteurs():
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.get(f"{api_service_url}/auteurs", headers=headers)
        response.raise_for_status()
        auteurs = response.json()
        nom_colonne = ["ID", "Nom"]
        return render_template('auteurs.jinja2', auteurs=auteurs, col=nom_colonne)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('auteurs.jinja2', error=str(e))

@app.route('/utilisateur/<utilisateur>')
def utilisateur(utilisateur):
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.get(f"{api_service_url}/utilisateur/{utilisateur}", headers=headers)
        response.raise_for_status()
        utilisateur_info = response.json()
        return render_template('utilisateur.jinja2', utilisateur=utilisateur_info)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('utilisateur.jinja2', error=str(e))

@app.route('/livres/siecle/<int:numero>')
def livres_par_siecle(numero):
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.get(f"{api_service_url}/livres/siecle/{numero}", headers=headers)
        response.raise_for_status()
        lst_livres = response.json()
        nom_colonne = ["ID", "Titre", "Résumé", "Date de publication", "Auteur", "Disponibilité"]
        return render_template('livres_siecle.jinja2', lst=lst_livres, col=nom_colonne, siecle=numero)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('livres_siecle.jinja2', error=str(e), siecle=numero)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5008, debug=True)
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Pour sécuriser la session Flask

# URL du service API
api_service_url = 'http://api_back:5000'

# Fonction pour obtenir le JWT
def get_jwt():
    return session.get('jwt')

@app.route('/')
def accueil():
    try:
        if 'jwt' in session:
            message = "Bienvenue sur l’interface utilisateur."
        else:
            message = "Vous devez vous connecter pour accéder à certaines fonctionnalités."
        return render_template('index.jinja2', message=message)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('index.jinja2', error=str(e))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    try:
        response = requests.post(
            f"{api_service_url}/login", 
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        token = response.json().get("token")
        if token:
            session['jwt'] = token  # Sauvegarder le JWT dans la session
            flash("Connexion réussie!", "success")
            return redirect(url_for("accueil"))
        else:
            flash("Erreur lors de la connexion.", "danger")
            return redirect(url_for("accueil"))
    except requests.exceptions.RequestException as e:
        flash(f"Erreur lors de la connexion : {e}", "danger")
        return redirect(url_for("accueil"))

@app.route('/logout')
def logout():
    session.pop('jwt', None)  # Supprimer le JWT à la déconnexion
    flash("Déconnexion réussie.", "success")
    return redirect(url_for('accueil'))

@app.route('/utilisateurs')
def utilisateurs():
    token = get_jwt()
    if not token:
        flash("Vous devez être connecté pour accéder à cette page.", "danger")
        return redirect(url_for("accueil"))

    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{api_service_url}/utilisateurs", headers=headers)
        response.raise_for_status()
        utilisateurs = response.json()
        nom_colonne = ["ID", "Nom", "Email", "Nombre de livres empruntés"]
        return render_template('utilisateurs.jinja2', utilisateurs=utilisateurs, col=nom_colonne)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('utilisateurs.jinja2', error=str(e))

@app.route('/livres')
def livres():
    token = get_jwt()
    if not token:
        flash("Vous devez être connecté pour accéder à cette page.", "danger")
        return redirect(url_for("accueil"))

    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{api_service_url}/livres", headers=headers)
        response.raise_for_status()
        lst_livres = response.json()
        nom_colonne = ["ID", "Titre", "Résumé", "Date de publication", "Auteur", "Disponibilité"]
        return render_template('livres.jinja2', lst=lst_livres, col=nom_colonne)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('livres.jinja2', error=str(e))

@app.route('/auteurs')
def auteurs():
    token = get_jwt()
    if not token:
        flash("Vous devez être connecté pour accéder à cette page.", "danger")
        return redirect(url_for("accueil"))

    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{api_service_url}/auteurs", headers=headers)
        response.raise_for_status()
        auteurs = response.json()
        nom_colonne = ["ID", "Nom"]
        return render_template('auteurs.jinja2', auteurs=auteurs, col=nom_colonne)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('auteurs.jinja2', error=str(e))

@app.route('/utilisateur/<utilisateur>')
def utilisateur(utilisateur):
    token = get_jwt()
    if not token:
        flash("Vous devez être connecté pour accéder à cette page.", "danger")
        return redirect(url_for("accueil"))

    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{api_service_url}/utilisateur/{utilisateur}", headers=headers)
        response.raise_for_status()
        utilisateur_info = response.json()
        return render_template('utilisateur.jinja2', utilisateur=utilisateur_info)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('utilisateur.jinja2', error=str(e))

@app.route('/livres/siecle/<int:numero>')
def livres_par_siecle(numero):
    token = get_jwt()
    if not token:
        flash("Vous devez être connecté pour accéder à cette page.", "danger")
        return redirect(url_for("accueil"))

    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{api_service_url}/livres/siecle/{numero}", headers=headers)
        response.raise_for_status()
        lst_livres = response.json()
        nom_colonne = ["ID", "Titre", "Résumé", "Date de publication", "Auteur", "Disponibilité"]
        return render_template('livres_siecle.jinja2', lst=lst_livres, col=nom_colonne, siecle=numero)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur lors de la connexion à l'API: {e}")
        return render_template('livres_siecle.jinja2', error=str(e), siecle=numero)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5008, debug=True)
"""