from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse
import sqlite3

app = FastAPI()

# Utility function to interact with the SQLite database
def execute_query(query, params=(), fetchone=False, commit=False):
    with sqlite3.connect("back/database/database.db") as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        if commit:
            conn.commit()
            return cur.lastrowid
        if fetchone:
            return cur.fetchone()
        return cur.fetchall()
    
@app.get('/')
async def index():
    return JSONResponse(content={'message':'Salut bienvenue sur mon api back'})

# Endpoint: Get all users
@app.get('/utilisateurs')
async def get_utilisateurs():
    utilisateurs = execute_query("SELECT * FROM utilisateurs")
    response = [
        {"id": u[0], "nom": u[1], "email": u[2], "livres_empruntes": u[3]} 
        for u in utilisateurs
    ]
    return JSONResponse(content=response)

# Endpoint: Get all books
@app.get('/livres')
async def get_livres():
    livres = execute_query("SELECT * FROM Livres")
    response = [
        {
            "id": l[0],
            "titre": l[1],
            "pitch": l[2],
            "date_public": l[3],
            "auteur_id": l[4],
            "emprunteur_id": l[5]
        } 
        for l in livres
    ]
    return JSONResponse(content=response)

# Endpoint: Get a specific user by ID or name
@app.get('/utilisateur/{utilisateur}')
async def get_utilisateur(utilisateur: str):
    if utilisateur.isdigit():
        result = execute_query("SELECT * FROM utilisateurs WHERE id = ?", (int(utilisateur),), fetchone=True)
    else:
        result = execute_query("SELECT * FROM utilisateurs WHERE nom = ?", (utilisateur,))
        if len(result) > 1:
            raise HTTPException(status_code=400, detail="Plusieurs utilisateurs portent ce nom.")
        elif result:
            result = result[0]
    
    if result:
        response = {"id": result[0], "nom": result[1], "email": result[2], "livres_empruntes": result[3]}
        return JSONResponse(content=response)
    raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")

# Endpoint: Get borrowed books of a user by ID or name
@app.get('/utilisateur/emprunts/{utilisateur}')
async def get_emprunts(utilisateur: str):
    if utilisateur.isdigit():
        utilisateur_id = int(utilisateur)
    else:
        user = execute_query("SELECT id FROM utilisateurs WHERE nom = ?", (utilisateur,), fetchone=True)
        if user:
            utilisateur_id = user[0]
        else:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")

    livres = execute_query("SELECT titre FROM Livres WHERE emprunteur_id = ?", (utilisateur_id,))
    response = [{"titre": livre[0]} for livre in livres]
    return JSONResponse(content=response)

@app.get('/livres/siecle/{numero}')
async def get_livres_par_siecle(numero: int):
    """
    Retourne les livres publiés dans un siècle donné.
    Le numéro du siècle est un entier (par exemple, 20 pour le XXe siècle).
    """
    if numero < 1 or numero > 21:  # Validation des siècles réalistes
        raise HTTPException(status_code=400, detail="Siècle invalide. Veuillez entrer un siècle entre 1 et 21.")
    
    # Calcul des bornes d'années pour le siècle
    start_year = (numero - 1) * 100 + 1
    end_year = start_year + 99

    # Requête SQLite : extrait l'année en prenant les 4 derniers caractères de la date
    livres = execute_query(
        """
        SELECT id, titre, pitch, date_public, auteur_id, emprunteur_id
        FROM Livres
        WHERE CAST(SUBSTR(date_public, -4) AS INTEGER) BETWEEN ? AND ?
        """,
        (start_year, end_year)
    )

    # Préparer la réponse
    response = [
        {
            "id": livre[0],
            "titre": livre[1],
            "pitch": livre[2],
            "date_public": livre[3],
            "auteur_id": livre[4],
            "emprunteur_id": livre[5]
        }
        for livre in livres
    ]

    if not response:
        raise HTTPException(status_code=404, detail=f"Aucun livre trouvé pour le {numero}ème siècle.")
    
    return JSONResponse(content=response)


# Endpoint: Add a user
@app.post('/utilisateur/ajouter')
async def ajouter_utilisateur(nom: str = Form(...), email: str = Form(...)):
    if not nom or not email:
        raise HTTPException(status_code=400, detail="Données invalides.")
    
    utilisateur_id = execute_query(
        "INSERT INTO utilisateurs (nom, email) VALUES (?, ?)", 
        (nom, email), 
        commit=True
    )
    response = {"id": utilisateur_id, "message": "Utilisateur ajouté avec succès."}
    return JSONResponse(content=response)

# Endpoint: Add a book
@app.post('/livres/ajouter')
async def ajouter_livre(titre: str = Form(...), pitch: str = Form(...), date_public: str = Form(...), auteur_nom: str = Form(...)):
    if not titre or not pitch or not date_public or not auteur_nom:
        raise HTTPException(status_code=400, detail="Données invalides.")

    auteur = execute_query("SELECT id FROM Auteurs WHERE nom_auteur = ?", (auteur_nom,), fetchone=True)
    if not auteur:
        auteur_id = execute_query("INSERT INTO Auteurs (nom_auteur) VALUES (?)", (auteur_nom,), commit=True)
    else:
        auteur_id = auteur[0]

    livre_id = execute_query(
        "INSERT INTO Livres (titre, pitch, date_public, auteur_id) VALUES (?, ?, ?, ?)",
        (titre, pitch, date_public, auteur_id),
        commit=True
    )

    response = {"id": livre_id, "message": "Livre ajouté avec succès."}
    return JSONResponse(content=response)

# Endpoint: Delete a user by ID or name
@app.delete('/utilisateur/{utilisateur}/supprimer')
async def supprimer_utilisateur(utilisateur: str):
    if utilisateur.isdigit():
        utilisateur_id = int(utilisateur)
    else:
        utilisateur = execute_query("SELECT id FROM utilisateurs WHERE nom = ?", (utilisateur,), fetchone=True)
        if not utilisateur:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
        utilisateur_id = utilisateur[0]

    execute_query("DELETE FROM utilisateurs WHERE id = ?", (utilisateur_id,), commit=True)
    response = {"message": "Utilisateur supprimé avec succès."}
    return JSONResponse(content=response)

# Endpoint: Borrow a book
@app.put('/utilisateur/{utilisateur_id}/emprunter/{livre_id}')
async def emprunter_livre(utilisateur_id: int, livre_id: int):
    livre = execute_query("SELECT emprunteur_id FROM Livres WHERE id = ?", (livre_id,), fetchone=True)
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé.")
    
    if livre[0]:
        raise HTTPException(status_code=400, detail="Ce livre est déjà emprunté.")

    utilisateur = execute_query("SELECT livres_empruntes FROM utilisateurs WHERE id = ?", (utilisateur_id,), fetchone=True)
    if utilisateur:
        nombre_livres_empruntes = utilisateur[0]
        if nombre_livres_empruntes >= 4:
            raise HTTPException(status_code=400, detail="Limite de livres empruntés atteinte.")
    execute_query("UPDATE Livres SET emprunteur_id = ? WHERE id = ?", (utilisateur_id, livre_id), commit=True)
    nouveaux_nombre_livres_empruntes = nombre_livres_empruntes + 1
    execute_query("UPDATE utilisateurs SET livres_empruntes = ? WHERE id = ?", (nouveaux_nombre_livres_empruntes, utilisateur_id), commit=True)
    response = {"message": "Livre emprunté avec succès."}
    return JSONResponse(content=response)

# Endpoint: Return a book
@app.put('/utilisateur/{utilisateur_id}/rendre/{livre_id}')
async def rendre_livre(utilisateur_id: int, livre_id: int):
    livre = execute_query("SELECT emprunteur_id FROM Livres WHERE id = ?", (livre_id,), fetchone=True)
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé.")
    
    if livre[0] != utilisateur_id:
        raise HTTPException(status_code=400, detail="Ce livre n'a pas été emprunté par cet utilisateur.")
    execute_query("UPDATE Livres SET emprunteur_id = NULL WHERE id = ?", (livre_id,), commit=True)
    utilisateur = execute_query("SELECT livres_empruntes FROM utilisateurs WHERE id = ?", (utilisateur_id,), fetchone=True)
    if utilisateur:
        nouveaux_nombre_livres_empruntes = utilisateur[0] - 1
        execute_query("UPDATE utilisateurs SET livres_empruntes = ? WHERE id = ?", (nouveaux_nombre_livres_empruntes, utilisateur_id), commit=True)

    response = {"message": "Livre rendu avec succès."}
    return JSONResponse(content=response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5010)
    