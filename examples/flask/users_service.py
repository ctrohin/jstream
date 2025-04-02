from jstreams import Stream, service, str_contains_ignore_case
from typing import Any, Optional

DEFAULT_USERS = {
    1: {"name": "Alice", "age": 30},
    2: {"name": "Bob", "age": 25},
}


@service()
class UserService:
    def __init__(self) -> None:
        self.users: dict[int, dict[str, Any]] = DEFAULT_USERS

    def get_max_user_id(self) -> int:
        if not self.users:
            return 0
        return max(self.users.keys())

    def create_user(self, user_data: dict[str, Any]) -> dict[str, Any]:
        user_id = self.get_max_user_id() + 1
        self.users[user_id] = user_data
        return {"user_id": user_id, "user_data": user_data}

    def get_user(self, user_id: int) -> Optional[dict[str, Any]]:
        if user_id not in self.users:
            raise ValueError("User not found")
        return {"user_id": user_id, "user_data": self.users[user_id]}

    def get_all_users(self) -> dict[int, dict[str, Any]]:
        return self.users

    def get_users_by_name(self, name: str) -> list[dict[str, Any]]:
        return (
            Stream(self.users.values())
            .filter(lambda u: str_contains_ignore_case(name)(u["name"]))
            .to_list()
        )
