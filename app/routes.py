import ast
import math
import operator
import secrets
import time
from functools import wraps

from flask import (
    Blueprint,
    abort,
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

SESSION_IDLE_TIMEOUT = 15 * 60


@main.before_app_request
def load_logged_in_student():
    """Load the student and expire inactive sessions."""
    g.student = None
    student_id = session.get("student_id")

    if student_id is None:
        return

    now = time.time()
    last_activity = session.get("last_activity")

    if (
        last_activity is None
        or now - last_activity >= SESSION_IDLE_TIMEOUT
    ):
        session.clear()
        return

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
        return

    session["last_activity"] = now


def login_required(view):
    """Require a signed-in student to access a page."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.student is None:
            return redirect(url_for("main.login"))

        return view(*args, **kwargs)

    return wrapped_view


def calculate_arithmetic(expression):
    """Calculate arithmetic without executing user-supplied Python code."""
    if not expression or len(expression) > 200:
        raise ValueError("Enter an expression of up to 200 characters.")

    tree = ast.parse(expression, mode="eval")

    if sum(1 for _ in ast.walk(tree)) > 64:
        raise ValueError("Expression is too complex.")

    operations = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    def evaluate(node):
        if isinstance(node, ast.Constant):
            if type(node.value) not in (int, float):
                raise ValueError("Only numbers are allowed.")

            value = node.value

        elif isinstance(node, ast.BinOp) and type(node.op) in operations:
            value = operations[type(node.op)](
                evaluate(node.left),
                evaluate(node.right),
            )

        elif isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.UAdd, ast.USub)
        ):
            operand = evaluate(node.operand)
            value = -operand if isinstance(node.op, ast.USub) else operand

        else:
            raise ValueError("Only arithmetic is allowed.")

        if not math.isfinite(value) or abs(value) > 1_000_000_000_000:
            raise ValueError("Number is outside the allowed range.")

        return value

    return evaluate(tree.body)


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
            session["last_activity"] = time.time()

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


@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Display and update the signed-in student's biography."""
    if "profile_csrf_token" not in session:
        session["profile_csrf_token"] = secrets.token_hex(32)

    error = None
    biography = ""

    if request.method == "POST":
        submitted_token = request.form.get("csrf_token", "")

        if not secrets.compare_digest(
            submitted_token.encode("utf-8"),
            session["profile_csrf_token"].encode("utf-8"),
        ):
            abort(400)

        biography = request.form.get("biography", "").strip()

        if len(biography) > 1000:
            error = "Please keep your biography within 1,000 characters."
        else:
            db = get_db()
            db.execute(
                """
                UPDATE students
                SET biography = ?
                WHERE id = ?
                """,
                (biography, g.student["id"]),
            )
            db.commit()

            return redirect(url_for("main.profile"))

    return render_template(
        "profile.html",
        student=g.student,
        biography=biography,
        error=error,
        csrf_token=session["profile_csrf_token"],
    )


@main.route("/calculator", methods=["GET", "POST"])
@login_required
def calculator():
    """Calculate arithmetic using a restricted expression parser."""
    if "calculator_csrf_token" not in session:
        session["calculator_csrf_token"] = secrets.token_hex(32)

    expression = ""
    result = None

    if request.method == "POST":
        submitted_token = request.form.get("csrf_token", "")

        if not secrets.compare_digest(
            submitted_token.encode("utf-8"),
            session["calculator_csrf_token"].encode("utf-8"),
        ):
            abort(400)

        expression = request.form.get("expression", "").strip()

        if not expression or len(expression) > 200:
            result = "Enter an expression of up to 200 characters."
        else:
            try:
                result = str(calculate_arithmetic(expression))
            except (
                SyntaxError,
                ValueError,
                TypeError,
                ArithmeticError,
                RecursionError,
            ):
                result = "Unable to calculate that expression."

    return render_template(
        "calculator.html",
        expression=expression,
        result=result,
        csrf_token=session["calculator_csrf_token"],
    )


@main.route("/logout")
def logout():
    """Clear the student's session and return home."""
    session.clear()
    return redirect(url_for("main.home"))


@main.route("/health")
def health():
    """Report application health."""
    return jsonify(status="healthy"), 200