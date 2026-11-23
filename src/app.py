import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = os.environ.get("TASKFLOW_DATABASE", str(BASE_DIR / "taskflow.db"))

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "taskflow-dev-key")


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'Média',
                status TEXT NOT NULL DEFAULT 'A Fazer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()


@app.route("/")
def index():
    status = request.args.get("status", "").strip()
    search = request.args.get("q", "").strip()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status in ("A Fazer", "Em Progresso", "Concluída"):
        query += " AND status = ?"
        params.append(status)

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += """
        ORDER BY CASE priority
            WHEN 'Alta' THEN 1
            WHEN 'Média' THEN 2
            ELSE 3
        END, id DESC
    """

    with get_db() as db:
        tasks = db.execute(query, params).fetchall()

        counts = {
            "total": db.execute(
                "SELECT COUNT(*) FROM tasks"
            ).fetchone()[0],

            "todo": db.execute(
                "SELECT COUNT(*) FROM tasks WHERE status='A Fazer'"
            ).fetchone()[0],

            "doing": db.execute(
                "SELECT COUNT(*) FROM tasks WHERE status='Em Progresso'"
            ).fetchone()[0],

            "done": db.execute(
                "SELECT COUNT(*) FROM tasks WHERE status='Concluída'"
            ).fetchone()[0],
        }

    return render_template(
        "index.html",
        tasks=tasks,
        counts=counts,
        selected_status=status,
        search=search
    )


@app.route("/tasks", methods=["POST"])
def create_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Média")

    if not title:
        flash("Informe um título para a tarefa.", "error")
        return redirect(url_for("index"))

    if priority not in ("Baixa", "Média", "Alta"):
        priority = "Média"

    with get_db() as db:
        db.execute(
            """
            INSERT INTO tasks (title, description, priority)
            VALUES (?, ?, ?)
            """,
            (title, description, priority)
        )
        db.commit()

    flash("Tarefa criada com sucesso!", "success")
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/update", methods=["POST"])
def update_task(task_id):
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Média")
    status = request.form.get("status", "A Fazer")

    if not title:
        flash("O título não pode ficar vazio.", "error")
        return redirect(url_for("index"))

    if priority not in ("Baixa", "Média", "Alta"):
        priority = "Média"

    if status not in ("A Fazer", "Em Progresso", "Concluída"):
        status = "A Fazer"

    with get_db() as db:
        db.execute(
            """
            UPDATE tasks
            SET title=?, description=?, priority=?, status=?
            WHERE id=?
            """,
            (title, description, priority, status, task_id)
        )
        db.commit()

    flash("Tarefa atualizada.", "success")
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    with get_db() as db:
        db.execute(
            "DELETE FROM tasks WHERE id=?",
            (task_id,)
        )
        db.commit()

    flash("Tarefa removida.", "success")
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
