from jstreams import Stream, service, str_contains_ignore_case
from typing import Any
from collections.abc import Iterable


class User:
    def __init__(self, user_id: int, name: str, age: int) -> None:
        """
        User class.
        Args:
            user_id (int): User id.
            name (str): User name.
            age (int): User age.
        """
        self.user_id = user_id
        self.name = name
        self.age = age

    def as_json(self) -> dict[str, Any]:
        """
        Convert user to json.
        Returns:
            dict[str, Any]: User in json format.
        """
        return {"user_id": self.user_id, "name": self.name, "age": self.age}


DEFAULT_USERS = {
    1: User(1, "Alice", 30),
    2: User(2, "Bob", 25),
    3: User(3, "Charlie", 35),
    4: User(4, "David", 28),
    5: User(5, "Eve", 22),
    6: User(6, "Frank", 40),
    7: User(7, "Grace", 32),
}


@service()
class UserService:
    def __init__(self) -> None:
        self.users: dict[int, User] = DEFAULT_USERS

    def get_max_user_id(self) -> int:
        """
        Get the maximum user id.
        Returns:
            int: Maximum user id.
        """
        if not self.users:
            return 0
        return max(self.users.keys())

    def create_user(self, name: str, age: int) -> User:
        """
        Create a new user.
        Args:
            name (str): User name.
            age (int): User age.
        Returns:
            User: Created user.
        """
        new_user = User(self.get_max_user_id() + 1, name, age)
        self.users[new_user.user_id] = new_user
        return new_user

    def get_user(self, user_id: int) -> User:
        """
        Get user by id.
        Args:
            user_id (int): User id.
        Returns:
            User: User.
        Raises:
            ValueError: If user not found.
        """
        if user_id not in self.users:
            raise ValueError("User not found")
        return self.users[user_id]

    def get_all_users(self) -> Iterable[User]:
        """
        Get all users.
        Returns:
            Iterable[User]: List of users.
        """
        return self.users.values()

    def get_users_by_name(self, name: str) -> list[User]:
        """
        Get users by name.
        Args:
            name (str): User name.
        Returns:
            list[User]: List of users.
        """
        return (
            Stream(self.users.values())
            .filter(lambda u: str_contains_ignore_case(name)(u.name))
            .to_list()
        )
