import jwt
import datetime
from flask import Flask, jsonify, request, Response
from pathlib import Path

app = Flask(__name__)

# Charger la clé privée
with open("private_key.pem", "r") as f:
    private_key = f.read()

# Charger la clé publique pour vérifier les JWT
with open("public_key.pem", "r") as f:
    public_key = f.read()

@app.route('/login', methods=['POST'])
def login():
    # Exemple de vérification d'identifiants
    username = request.form['username']
    password = request.form['password']

    # Ici tu devrais vérifier les informations d'identification
    if username == 'admin' and password == 'password':
        # Créer un JWT signé avec RS256
        payload = {
            "user_id": 1,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Expiration dans 1 heure
        }

        token = jwt.encode(payload, private_key, algorithm='RS256')
        return jsonify({"token": token})

    return Response("Unauthorized", status=401)

@app.route('/protected', methods=['GET'])
def protected():
    # Vérifier le JWT dans les headers Authorization
    token = request.headers.get('Authorization')
    if not token:
        return Response("Missing token", status=400)

    try:
        # Vérifier et décoder le token avec la clé publique
        decoded = jwt.decode(token, public_key, algorithms=['RS256'])
        return jsonify({"message": "Access granted", "user_id": decoded['user_id']})
    except jwt.ExpiredSignatureError:
        return Response("Token expired", status=401)
    except jwt.InvalidTokenError:
        return Response("Invalid token", status=401)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
