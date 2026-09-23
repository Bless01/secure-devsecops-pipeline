from functools import wraps

from flask import (
    Blueprint,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from app.db import get_db

main = Blueprint("main", __name__)


@main.before_app_request
def load_logged_in_student():
    """Load the student associated with the current session."""
    student_id = session.get("student_id")
    g.student = None

    if student_id is not None:
        g.student = get_db().execute(
            """
            SELECT id, student_number, full_name, email,
                   program, academic_level, phone, biography
            FROM students
            WHERE id = ?
            """,
            (student_id,),
        ).fetchone()

        if g.student is None:
            session.clear()


def login_required(view):
    """Require a signed-in student to access a page."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.student is None:
            return redirect(url_for("main.login"))

        return view(*args, **kwargs)

    return wrapped_view


@main.route("/")
def home():
    """Display the Blessings University homepage."""
    return render_template("index.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    """Check the student's credentials and start a session."""
    if g.student is not None:
        return redirect(url_for("main.dashboard"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        student = get_db().execute(
            """
            SELECT id, password_hash
            FROM students
            WHERE student_number = ? OR email = ?
            """,
            (username, username),
        ).fetchone()

        if student is None or not check_password_hash(
            student["password_hash"], password
        ):
            error = "Invalid student ID, email, or password."
        else:
            session.clear()
            session["student_id"] = student["id"]
            return redirect(url_for("main.dashboard"))

    return render_template("login.html", error=error)


@main.route("/dashboard")
@login_required
def dashboard():
    """Display the signed-in student's dashboard."""
    return render_template("dashboard.html", student=g.student)


@main.route("/grades")
@login_required
def grades():
    """Read only the signed-in student's course results."""
    results = get_db().execute(
        """
        SELECT courses.course_code,
               courses.title,
               courses.credits,
               enrollments.semester,
               grades.score,
               grades.letter_grade
        FROM enrollments
        JOIN courses ON courses.id = enrollments.course_id
        LEFT JOIN grades ON grades.enrollment_id = enrollments.id
        WHERE enrollments.student_id = ?
        ORDER BY enrollments.semester DESC, courses.course_code
        """,
        (g.student["id"],),
    ).fetchall()

    return render_template(
        "grades.html",
        student=g.student,
        results=results,
    )


@main.route("/profile")
@login_required
def profile():
    """Display the signed-in student's profile."""
    return render_template("profile.html", student=g.student)


@main.route("/logout")
def logout():
    """Clear the student's session and return home."""
    session.clear()
    return redirect(url_for("main.home"))


@main.route("/health")
def health():
    """Return the application status."""
    return jsonify({"status": "healthy"}), 200