# FastAPI sample code using jstreams
from typing import Any
from fastapi import FastAPI
from users_view import UsersView
from jstreams import InjectedDependency, inject

app = FastAPI()

# FastAPI doesn't cope well with decorated routes, so in our case, we need to use an injected dependency object.
# Using the InjectedDependency class is more economical than injector().get() or inject() since once the dependency
# is resolved, it is also cached.
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


# We can also use the InjectedDependency class as a default parameter for the route function.
@app.get("/get_users_by_name/{name}")
def get_users_by_name(
    name: str, users=InjectedDependency(UsersView)
) -> list[dict[str, Any]]:
    return users().get_users_by_name(name)


# Or we can use inject() directly. This is also OK, as the default initializer for the parameter will
# only be called once.
@app.get("/get_users_by_name_alias/{name}")
def get_users_by_name_alias(name: str, users=inject(UsersView)) -> list[dict[str, Any]]:
    return users.get_users_by_name(name)
