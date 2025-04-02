from flask import Flask
from jstreams import inject
from users_service import UserService

app = Flask(__name__)


@app.route("/")
def hello() -> str:
    return "Hello, World!"


@app.route("/get_user/<int:user_id>")
def get_user(user_id: int) -> dict[str, str]:
    try:
        return inject(UserService).get_user(user_id)
    except ValueError as e:
        return {"error": str(e), "user_id": user_id}


@app.route("/create_user/<name>/<int:age>")
def create_user(name: str, age: int) -> dict[str, str]:
    try:
        return inject(UserService).create_user({"name": name, "age": age})
    except ValueError as e:
        return {"error": str(e), "name": name, "age": age}


@app.route("/get_all_users")
def get_all_users() -> dict[int, dict[str, str]]:
    return inject(UserService).get_all_users()


@app.route("/get_users_by_name/<name>")
def get_users_by_name(name: str) -> dict[int, dict[str, str]]:
    return inject(UserService).get_users_by_name(name)
