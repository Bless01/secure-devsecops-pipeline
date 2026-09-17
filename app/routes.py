from flask import Blueprint, jsonify, redirect, render_template, request, url_for

main = Blueprint("main", __name__)


@main.route("/")
def home():
    """Display the Blessings University homepage."""
    return render_template("index.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    """Display the login page and open the visual student dashboard."""
    if request.method == "POST":
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@main.route("/dashboard")
def dashboard():
    """Display the student dashboard."""
    return render_template("dashboard.html")


@main.route("/grades")
def grades():
    """Display the student's grades."""
    return render_template("grades.html")


@main.route("/profile")
def profile():
    """Display the student's profile."""
    return render_template("profile.html")


@main.route("/logout")
def logout():
    """Return the student to the homepage."""
    return redirect(url_for("main.home"))


@main.route("/health")
def health():
    """Return the current application status."""
    return jsonify({"status": "healthy"}), 200