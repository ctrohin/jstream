# FastAPI sample code using jstreams
from typing import Any
from fastapi import FastAPI
from users_view import UsersView
from jstreams import InjectedDependency

app = FastAPI()

users_view = InjectedDependency(UsersView)


@app.get("/")
def hello() -> str:
    return "Hello, World!"


@app.get("/get_user/{user_id}")
def get_user(user_id: int) -> dict[str, str]:
    try:
        return users_view().get_user(user_id)
    except ValueError as e:
        return {"error": str(e), "user_id": user_id}


@app.get("/create_user/{name}/{age}")
def create_user(name: str, age: int) -> dict[str, str]:
    try:
        return users_view().create_user({"name": name, "age": age})
    except ValueError as e:
        return {"error": str(e), "name": name, "age": age}


@app.get("/get_all_users")
def get_all_users() -> list[dict[str, Any]]:
    return users_view().get_users()


@app.get("/get_users_by_name/{name}")
def get_users_by_name(name: str) -> list[dict[str, Any]]:
    return users_view().get_users_by_name(name)
