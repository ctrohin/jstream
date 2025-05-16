from threading import Thread
from time import sleep
import sys
from typing import Optional

sys.path.append(".")

from jstreams import (
    inject_args,
    event,
    managed_events,
    on_event,
    service,
    all_args,
)


# We declare a User class decorated with @all_args to automatically generate the `all` method allowing us
# to create instances of User with all its attributes.
@all_args()
class User:
    name: str
    age: int
    email: str

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"User(name={self.name}, age={self.age}, email={self.email})"


# Then we declare two events: AddUserEvent and DeleteUserEvent. These events will be used to notify the UserService
class AddUserEvent:
    def __init__(self, user: User):
        self.user = user


class DeleteUserEvent:
    def __init__(self, user: User):
        self.user = user


# We decorate the UserService class with @managed_events to automatically manage the events
# and @service to make it a service that can be injected into other classes.
# The UserService class has a list of users and methods to get users, add users, and delete users.
@managed_events()
@service()
class UserService:
    def __init__(self):
        self.users = []

    def get_users(self) -> list[User]:
        return self.users

    def get_user_by_name(self, name: str) -> Optional[User]:
        for user in self.users:
            if user.name == name:
                return user
        return None

    # We use the @on_event decorator to listen to the events and execute the corresponding methods
    # The first method listens to the AddUserEvent and adds the user to the list of users
    @on_event(AddUserEvent)
    def add_user(self, user: AddUserEvent) -> None:
        print(f"Adding user {user.user}")
        self.users.append(user.user)
        print(self.users)

    # The second method listens to the DeleteUserEvent and removes the user from the list of users
    @on_event(DeleteUserEvent)
    def delete_user(self, user: DeleteUserEvent) -> None:
        print(f"Deleting user {user.user}")
        self.users.remove(user.user)
        print(self.users)


# We create two threads: AddUsersThread and RevmoveUersThread
# The AddUsersThread adds users to the UserService every 2 seconds
# The RevmoveUersThread removes users from the UserService every 3 seconds
class AddUsersThread(Thread):
    def __init__(self):
        super().__init__()

    def run(self) -> None:
        for i in range(10):
            sleep(2)
            print(f"Adding user {i}")
            user = User.all(name=f"user{i}", age=i, email=f"user{i}@gmail.com")
            # We use the event function to publish the AddUserEvent
            # This will trigger the add_user method in the UserService
            event(AddUserEvent).publish(AddUserEvent(user))


class RevmoveUersThread(Thread):
    # Since we need to inject the UserService into the RevmoveUersThread, we use the @inject_args decorator
    @inject_args({"user_service": UserService})
    def __init__(self, user_service: UserService):
        super().__init__()
        self.user_service = user_service

    def run(self) -> None:
        for i in range(10):
            sleep(3)
            print(f"Removing user {i}")
            user = self.user_service.get_users()[0]
            # We use the event function to publish the DeleteUserEvent
            # This will trigger the delete_user method in the UserService
            event(DeleteUserEvent).publish(DeleteUserEvent(user))


if __name__ == "__main__":
    AddUsersThread().start()
    RevmoveUersThread().start()
