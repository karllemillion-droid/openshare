import os
import logging
import uuid  
import boto3
from botocore.config import Config as BotoConfig

from flask import (
    Flask, render_template, request,
    redirect, url_for, send_from_directory, flash, abort, Response
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename  
from cryptography.fernet import Fernet  

from config import Config
from database import get_db, init_db
from security import validate_file, safe_filename
from headers import init_security_headers
from auth import auth_bp, init_auth
from limiter import limiter, init_limiter, setup_logging

from dotenv import load_dotenv
load_dotenv()  # Charge le fichier .env

# 1. INITIALISATION DE L'APPLICATION FLASK 🚨
app = Flask(__name__)
app.config.from_object(Config)

# 2. CONFIGURATION DU CHIFFREMENT 🚨
app.config["ENCRYPTION_KEY"] = b"qaSP-KO0zYRUbehLkQ4jsQzw8Qw94gyRuxLlurTr6c4="
fernet = Fernet(app.config["ENCRYPTION_KEY"])

# 3. CONFIGURATION CLOUDFLARE R2 / S3 🚨
app.config["R2_ACCOUNT_ID"] = os.getenv("R2_ACCOUNT_ID", "TON_ACCOUNT_ID_CLOUDFLARE")
app.config["R2_ACCESS_KEY"] = os.getenv("R2_ACCESS_KEY", "TA_CLE_D_ACCES")
app.config["R2_SECRET_KEY"] = os.getenv("R2_SECRET_KEY", "TA_CLE_SECRETE")
app.config["R2_BUCKET_NAME"] = os.getenv("R2_BUCKET_NAME", "openshare-storage")

s3_client = boto3.client(
    "s3",
    endpoint_url=f"https://{app.config['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
    aws_access_key_id=app.config["R2_ACCESS_KEY"],
    aws_secret_access_key=app.config["R2_SECRET_KEY"],
    config=BotoConfig(signature_version="s3v4"),
    region_name="auto"
)

# ── Extensions sécurité ────────────────────────────────────────────────────────
init_security_headers(app)   # CSRF + headers HTTP
init_auth(app)               # Flask-Login (qui enregistre déjà auth_bp)
init_limiter(app)            # Rate limiting

app.register_blueprint(auth_bp)

# ── Routes principales ────────────────────────────────────────────────────────

@app.route("/")
def index():
    conn = get_db()
    files = conn.execute(
        "SELECT f.*, u.username FROM files f "
        "LEFT JOIN users u ON f.owner_id = u.id "
        "ORDER BY f.uploaded_at DESC"
    ).fetchall()
    conn.close()
    return render_template("index.html", files=files)


def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'zip', 'rar', '7z', 'pdf', 'mp3', 'wav', 'mp4', 'mkv', 'txt', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """Formulaire d'upload et traitement vers Cloudflare R2 avec Chiffrement."""
    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            flash("Aucun fichier sélectionné.", "error")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Type de fichier non autorisé.", "error")
            return redirect(request.url)

        custom_name = request.form.get("custom_filename")
        original_ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""

        if custom_name and custom_name.strip():
            if not custom_name.lower().endswith(f".{original_ext}"):
                chosen_name = f"{custom_name.strip()}.{original_ext}"
            else:
                chosen_name = custom_name.strip()
        else:
            chosen_name = file.filename

        original_name = secure_filename(chosen_name)
        stored_name = f"{uuid.uuid4().hex}.{original_ext}"

        # 1. Chiffrement en mémoire
        file_data = file.read()
        encrypted_data = fernet.encrypt(file_data)

        # 2. Envoi direct dans le Cloud Storage (R2)
        try:
            s3_client.put_object(
                Bucket=app.config["R2_BUCKET_NAME"],
                Key=stored_name,
                Body=encrypted_data,
                ContentType=file.content_type or "application/octet-stream"
            )
        except Exception as e:
            flash(f"Erreur lors de l'envoi vers le stockage cloud : {e}", "error")
            return redirect(request.url)

        # 3. Métadonnées dans la base de données
        file_size = len(encrypted_data)
        mimetype = file.content_type

        conn = get_db()
        conn.execute(
            "INSERT INTO files (filename, original, size, mimetype, owner_id) VALUES (?, ?, ?, ?, ?)",
            (stored_name, original_name, file_size, mimetype, current_user.id)
        )
        conn.commit()
        conn.close()

        flash(f"« {original_name} » uploadé, chiffré et stocké dans le cloud !", "success")
        return redirect(url_for("index"))

    return render_template("upload.html")


@app.route("/download/<int:file_id>")
@limiter.limit("30 per hour")
def download(file_id: int):
    """Téléchargement et déchiffrement à la volée depuis Cloudflare R2."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM files WHERE id = ?", (file_id,)
    ).fetchone()
    conn.close()

    if row is None:
        abort(404)

    try:
        # 1. Récupération du fichier chiffré depuis Cloudflare R2
        s3_response = s3_client.get_object(
            Bucket=app.config["R2_BUCKET_NAME"],
            Key=row["filename"]
        )
        encrypted_data = s3_response["Body"].read()

        # 2. Déchiffrement à la volée
        decrypted_data = fernet.decrypt(encrypted_data)

    except Exception as e:
        flash("Erreur lors de la récupération ou du déchiffrement du fichier.", "error")
        return redirect(url_for("index"))

    # 3. Renvoyer le fichier déchiffré au client
    return Response(
        decrypted_data,
        mimetype=row["mimetype"],
        headers={
            "Content-Disposition": f"attachment; filename={row['original']}"
        }
    )


@app.route("/files")
def list_files():
    conn = get_db()
    files = conn.execute(
        "SELECT f.*, u.username FROM files f "
        "LEFT JOIN users u ON f.owner_id = u.id "
        "ORDER BY f.uploaded_at DESC"
    ).fetchall()
    conn.close()
    return render_template("files.html", files=files)


@app.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete(file_id: int):
    """Suppression dans le cloud R2 et en base de données."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM files WHERE id = ?", (file_id,)
    ).fetchone()

    if row is None:
        conn.close()
        abort(404)

    # Vérification de la propriété
    if row["owner_id"] != current_user.id:
        conn.close()
        abort(403)

    # 1. Suppression dans Cloudflare R2
    try:
        s3_client.delete_object(
            Bucket=app.config["R2_BUCKET_NAME"],
            Key=row["filename"]
        )
    except Exception as e:
        print(f"Erreur lors de la suppression sur R2: {e}")

    # 2. Suppression en base de données
    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    flash("Fichier supprimé avec succès.", "success")
    return redirect(url_for("index"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        flash("Paramètres mis à jour avec succès !", "success")
        return redirect(url_for("settings"))
        
    return render_template("settings.html")


# ── Gestion des erreurs ────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

@app.errorhandler(413)
def file_too_large(e):
    flash("Fichier trop volumineux (max 16 Mo).", "error")
    return redirect(url_for("upload"))


# ── Lancement ──────────────────────────────────────────────────────────────────
init_db()

if __name__ == "__main__":
    if app.config.get("UPLOAD_FOLDER"):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    setup_logging(app)
    app.run(debug=True)