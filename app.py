from flask import Flask, jsonify, request
import sqlite3
import os

app = Flask(__name__)

# 🔗 Connexion SQLite
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# 🔹 INIT DB (création automatique)
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Table prestataires
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prestataires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        service TEXT,
        description TEXT,
        telephone TEXT,
        note REAL,
        ville TEXT
    )
    """)

    # Table users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        telephone TEXT
    )
    """)

    # Table paiements
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paiements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        prestataire_id INTEGER,
        statut TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    # 🔥 Ajouter données si vide
    cursor.execute("SELECT COUNT(*) FROM prestataires")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO prestataires (nom, service, description, telephone, note, ville)
        VALUES 
        ('Kouassi Auto', 'Technicien auto', 'Réparation moteur et diagnostic', '0700000001', 4.5, 'Bouaké'),
        ('Hotel Ivoire Bouaké', 'Hôtellerie', 'Chambres modernes climatisées', '0700000002', 4.2, 'Bouaké'),
        ('Location Express', 'Location véhicule', 'Voitures avec chauffeur', '0700000003', 4.7, 'Bouaké'),
        ('Sidik Tech', 'Maintenance informatique', 'Réparation PC et réseaux', '0700000004', 5.0, 'Bouaké')
        """)
        conn.commit()

    conn.close()

# 🔹 ROUTE 1 : Liste prestataires
@app.route('/prestataires', methods=['GET'])
def get_prestataires():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, service, description, note, ville FROM prestataires")

    data = []
    for row in cursor.fetchall():
        data.append(dict(row))

    conn.close()
    return jsonify(data)

# 🔹 ROUTE 2 : Détail + blocage contact
@app.route('/prestataire/<int:prestataire_id>/<int:user_id>', methods=['GET'])
def get_prestataire(prestataire_id, user_id):
    conn = get_db()
    cursor = conn.cursor()

    # Vérifier paiement
    cursor.execute("""
        SELECT * FROM paiements 
        WHERE user_id=? AND prestataire_id=? AND statut='valide'
    """, (user_id, prestataire_id))

    paiement = cursor.fetchone()

    # Récupérer prestataire
    cursor.execute("SELECT * FROM prestataires WHERE id=?", (prestataire_id,))
    prestataire = cursor.fetchone()

    if not prestataire:
        return jsonify({"error": "Prestataire introuvable"}), 404

    prestataire = dict(prestataire)

    # Bloquer ou afficher numéro
    if paiement is None:
        prestataire["telephone"] = "🔒 Paiement requis"

    conn.close()
    return jsonify(prestataire)

# 🔹 ROUTE 3 : Paiement (simulation)
@app.route('/payer', methods=['POST'])
def payer():
    data = request.json

    user_id = data.get("user_id")
    prestataire_id = data.get("prestataire_id")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO paiements (user_id, prestataire_id, statut)
        VALUES (?, ?, 'valide')
    """, (user_id, prestataire_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Paiement validé"})

# 🔹 ROUTE 4 : Créer utilisateur
@app.route('/user', methods=['POST'])
def create_user():
    data = request.json

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (nom, telephone)
        VALUES (?, ?)
    """, (data.get("nom"), data.get("telephone")))

    conn.commit()
    conn.close()

    return jsonify({"message": "Utilisateur créé"})

# 🔹 ROUTE 5 : Historique paiements
@app.route('/paiements/<int:user_id>', methods=['GET'])
def get_paiements(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, pr.nom, pr.service, p.date
        FROM paiements p
        JOIN prestataires pr ON p.prestataire_id = pr.id
        WHERE p.user_id = ?
    """, (user_id,))

    data = []
    for row in cursor.fetchall():
        data.append({
            "id": row[0],
            "nom": row[1],
            "service": row[2],
            "date": row[3]
        })

    conn.close()
    return jsonify(data)

# 🔹 Lancement
if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))