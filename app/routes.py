from flask import Blueprint, jsonify, render_template

main = Blueprint("main", __name__)


@main.route("/")
def home():
    """Display the application home page."""
    return render_template("index.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    """Display the login page."""
    return render_template("login.html")


@main.route("/health")
def health():
    """Return the current application status."""
    return jsonify({"status": "healthy"}), 200
