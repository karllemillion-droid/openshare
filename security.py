import os
import uuid
from werkzeug.utils import secure_filename
from config import Config

DANGEROUS_EXTENSIONS = {
    "exe", "bat", "sh", "php", "js", "vbs",
    "ps1", "msi", "cmd", "com", "scr", "jar", "app",
}

def validate_file(file) -> tuple[bool, str]:
    """
    Valide un fichier uploadé sur 2 niveaux :
      1. Présence et nom valide
      2. Extension sur liste blanche + non dangereuse
    (Validation MIME désactivée pour compatibilité Windows)
    """
    filename = file.filename or ""

    if not filename or "." not in filename:
        return False, "Nom de fichier invalide."

    ext = filename.rsplit(".", 1)[1].lower()

    if ext in DANGEROUS_EXTENSIONS:
        return False, f"Type de fichier dangereux (.{ext} interdit)."

    if ext not in Config.ALLOWED_EXTENSIONS:
        return False, f"Extension .{ext} non autorisée."

    return True, ""


def safe_filename(original: str) -> tuple[str, str]:
    """
    Retourne (stored_name, original_name) :
    - stored_name : UUID + extension, jamais devinable
    - original_name : nom nettoyé pour l'affichage
    """
    clean = secure_filename(original)
    ext = clean.rsplit(".", 1)[1].lower() if "." in clean else "bin"
    stored = f"{uuid.uuid4().hex}.{ext}"
    return stored, clean
