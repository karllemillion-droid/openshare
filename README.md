# OpenShare · MVP

Plateforme simple de partage de fichiers — Flask + SQLite.

## Lancement rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'application
python app.py
```

Ouvrir ensuite : http://127.0.0.1:5000

## Structure

```
openshare/
├── app.py          # Routes Flask principales
├── config.py       # Configuration (taille max, extensions, chemins)
├── database.py     # Init SQLite + helper get_db()
├── requirements.txt
├── templates/
│   ├── base.html   # Layout partagé
│   ├── index.html  # Liste des fichiers
│   ├── upload.html # Formulaire d'upload
│   └── 404.html
├── static/css/
│   └── style.css
└── uploads/        # Fichiers déposés (généré automatiquement)
```

## Routes

| Route              | Méthode | Description                   |
|--------------------|---------|-------------------------------|
| `/`                | GET     | Liste tous les fichiers        |
| `/upload`          | GET     | Formulaire d'upload            |
| `/upload`          | POST    | Traitement du fichier          |
| `/download/<id>`   | GET     | Téléchargement par ID          |

## Sécurité (MVP)

- `secure_filename()` pour nettoyer les noms de fichiers
- UUID aléatoire comme nom de stockage (évite les collisions)
- Whitelist d'extensions autorisées
- Limite de taille (16 Mo) avec gestion d'erreur 413
- Requêtes SQLite paramétrées (protection SQL injection)

## Prochaines étapes

- [ ] Authentification utilisateur
- [ ] Suppression de fichiers
- [ ] Stockage cloud (S3 / Cloudinary)
- [ ] Pagination de la liste
- [ ] Scan antivirus (ClamAV)
