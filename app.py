from flask import Flask, jsonify, request
import mysql.connector
import os

app = Flask(__name__)

# 🔗 Connexion MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="bouake_services"
)

# 🔹 ROUTE 1 : Liste des prestataires
@app.route('/prestataires', methods=['GET'])
def get_prestataires():
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, nom, service, description, note, ville 
        FROM prestataires
    """)
    data = cursor.fetchall()
    return jsonify(data)


# 🔹 ROUTE 2 : Détail + blocage contact
@app.route('/prestataire/<int:prestataire_id>/<int:user_id>', methods=['GET'])
def get_prestataire(prestataire_id, user_id):
    cursor = db.cursor(dictionary=True)

    # Vérifier paiement
    cursor.execute("""
        SELECT * FROM paiements 
        WHERE user_id=%s AND prestataire_id=%s AND statut='valide'
    """, (user_id, prestataire_id))
    paiement = cursor.fetchone()

    # Récupérer prestataire
    cursor.execute("SELECT * FROM prestataires WHERE id=%s", (prestataire_id,))
    prestataire = cursor.fetchone()

    if not prestataire:
        return jsonify({"error": "Prestataire introuvable"}), 404

    # Bloquer ou afficher numéro
    if paiement is None:
        prestataire["telephone"] = "🔒 Paiement requis"

    return jsonify(prestataire)


# 🔹 ROUTE 3 : Simuler paiement (temporaire)
@app.route('/payer', methods=['POST'])
def payer():
    data = request.json

    user_id = data.get("user_id")
    prestataire_id = data.get("prestataire_id")

    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO paiements (user_id, prestataire_id, statut)
        VALUES (%s, %s, 'valide')
    """, (user_id, prestataire_id))

    db.commit()

    return jsonify({"message": "Paiement enregistré"})


# 🔹 ROUTE 4 : Créer utilisateur
@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    nom = data.get("nom")
    telephone = data.get("telephone")

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO users (nom, telephone)
        VALUES (%s, %s)
    """, (nom, telephone))
    db.commit()

    return jsonify({"message": "Utilisateur créé"})


# 🔹 ROUTE 5 : Historique paiements
@app.route('/paiements/<int:user_id>', methods=['GET'])
def get_paiements(user_id):
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.id, pr.nom, pr.service, p.date
        FROM paiements p
        JOIN prestataires pr ON p.prestataire_id = pr.id
        WHERE p.user_id = %s
    """, (user_id,))

    return jsonify(cursor.fetchall())


# 🔹 Lancement serveur
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)