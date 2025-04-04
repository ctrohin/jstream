from typing import Any
from users_service import UserService
from jstreams import Stream, inject_args, service


@service()
class UsersView:
    @inject_args({"user_service": UserService})
    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    def get_users(self) -> list[dict[str, Any]]:
        """
        Get all users.
        Returns:
            list[dict[str, Any]]: List of users.
        """
        return (
            Stream(self.user_service.get_all_users())
            .map(lambda e: e.as_json())
            .to_list()
        )

    def get_user(self, user_id: int) -> dict[str, Any]:
        """
        Get user by id.
        Args:
            user_id (int): User id.
        Returns:
            dict[str, Any]: User.
        Raises:
            ValueError: If user not found.
        """
        return self.user_service.get_user(user_id).as_json()

    def create_user(self, name: str, age: int) -> dict[str, Any]:
        """
        Create user.
        Args:
            name (str): User name.
            age (int): User age.
        Returns:
            dict[str, Any]: User.
        """
        return self.user_service.create_user(name, age).as_json()

    def get_users_by_name(self, name: str) -> list[dict[str, Any]]:
        """
        Get users by name.
        Args:
            name (str): User name.
        Returns:
            list[dict[str, Any]]: List of users.
        """
        return (
            Stream(self.user_service.get_users_by_name(name))
            .map(lambda e: e.as_json())
            .to_list()
        )
