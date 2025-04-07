# Flask API example using jstreams
from typing import Any
from flask import Flask
from jstreams import inject_args
from users_view import UsersView

app = Flask(__name__)


@app.route("/")
def hello() -> str:
    return "Hello, World!"


@app.route("/get_user/<int:user_id>")
@inject_args({"users_view": UsersView})
def get_user(user_id: int, users_view: UsersView) -> dict[str, str]:
    try:
        return users_view.get_user(user_id)
    except ValueError as e:
        return {"error": str(e), "user_id": user_id}


@app.route("/create_user/<name>/<int:age>")
@inject_args({"users_view": UsersView})
def create_user(name: str, age: int, users_view: UsersView) -> dict[str, str]:
    try:
        return users_view.create_user({"name": name, "age": age})
    except ValueError as e:
        return {"error": str(e), "name": name, "age": age}


@app.route("/get_all_users")
@inject_args({"users_view": UsersView})
def get_all_users(users_view: UsersView) -> list[dict[str, Any]]:
    return users_view.get_users()


@app.route("/get_users_by_name/<name>")
@inject_args({"users_view": UsersView})
def get_users_by_name(name: str, users_view: UsersView) -> list[dict[str, Any]]:
    return users_view.get_users_by_name(name)
