import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from database import get_db

login_manager = LoginManager()
auth_bp = Blueprint("auth", __name__)


class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get_by_id(user_id):
        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if row:
            return User(row["id"], row["username"], row["password_hash"])
        return None

    @staticmethod
    def get_by_username(username):
        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if row:
            return User(row["id"], row["username"], row["password_hash"])
        return None

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())


def init_auth(app):
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Connectez-vous pour accéder à cette page."
    login_manager.login_message_category = "error"

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ── Routes d'authentification ─────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm", "")

        # Validations
        if not username or len(username) < 3:
            flash("Le nom d'utilisateur doit faire au moins 3 caractères.", "error")
            return redirect(request.url)

        if len(password) < 8:
            flash("Le mot de passe doit faire au moins 8 caractères.", "error")
            return redirect(request.url)

        if password != confirm:
            flash("Les mots de passe ne correspondent pas.", "error")
            return redirect(request.url)

        if User.get_by_username(username):
            flash("Ce nom d'utilisateur est déjà pris.", "error")
            return redirect(request.url)

        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        conn.close()

        flash("Compte créé ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.get_by_username(username)

        # Vérification en temps constant (évite les timing attacks)
        if user and user.check_password(password):
            login_user(user)
            flash(f"Bienvenue, {user.username} !", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))

        flash("Identifiants incorrects.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for("index"))
