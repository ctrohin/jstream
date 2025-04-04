# Flask API example using jstreams
from typing import Any
from flask import Flask
from jstreams import InjectedDependency
from users_view import UsersView

app = Flask(__name__)

users_view = InjectedDependency(UsersView)


@app.route("/")
def hello() -> str:
    return "Hello, World!"


@app.route("/get_user/<int:user_id>")
def get_user(user_id: int) -> dict[str, str]:
    try:
        return users_view().get_user(user_id)
    except ValueError as e:
        return {"error": str(e), "user_id": user_id}


@app.route("/create_user/<name>/<int:age>")
def create_user(name: str, age: int) -> dict[str, str]:
    try:
        return users_view().create_user({"name": name, "age": age})
    except ValueError as e:
        return {"error": str(e), "name": name, "age": age}


@app.route("/get_all_users")
def get_all_users() -> list[dict[str, Any]]:
    return users_view().get_users()


@app.route("/get_users_by_name/<name>")
def get_users_by_name(name: str) -> list[dict[str, Any]]:
    return users_view().get_users_by_name(name)
