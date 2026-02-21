import os
from typing import Any, Final
from json import load

JSTREAMS_PROFILE: Final[str] = "JSTREAMS_PROFILE"
JSTREAMS_PROFILE_LOWER: Final[str] = "jstreams_profile"
JSTREAMS_PROFILE_CAMEL: Final[str] = "jstreamsProfile"

JSTREAMS_PACKAGES: Final[str] = "JSTREAMS_PACKAGES"
JSTREAMS_PACKAGES_LOWER: Final[str] = "jstreams_packages"
JSTREAMS_PACKAGES_CAMEL: Final[str] = "jstreamsPackages"

JSTREAMS_CONFIG_JSON: Final[str] = "JSTREAMS_CONFIG_JSON"
DEFAULT_FILE: Final[str] = "jstreams.json"

JSTREAMS_RAISE_BEAN_ERRORS: Final[str] = "JSTREAMS_RAISE_BEAN_ERRORS"
JSTREAMS_RAISE_BEAN_ERRORS_LOWER: Final[str] = "jstreams_raise_bean_errors"
JSTREAMS_RAISE_BEAN_ERRORS_CAMEL: Final[str] = "jstreamsRaiseBanErrors"


def get_env_config_file() -> str:
    return os.getenv(JSTREAMS_CONFIG_JSON, DEFAULT_FILE)


class JStreamsEnv:
    """
    Class that holds all the environment variables used by JStreams
    """

    __slots__ = ("__config", "__variables")

    def __init__(self) -> None:
        self.__config: dict[str, Any] = {}
        self.__variables: dict[str, Any] = {}

    def initialize(self) -> None:
        self.__load_config()

    def __load_config(self) -> None:
        if profile := self.__get_env_profile() is not None:
            self.__config[JSTREAMS_PROFILE] = profile

        if packages := self.__get_env_packages() is not None:
            self.__config[JSTREAMS_PACKAGES] = packages

        config_file = get_env_config_file()
        if os.path.exists(config_file):
            try:
                with open(config_file, encoding="utf-8") as f:
                    config = load(f)
                    if self.__config.get(JSTREAMS_PROFILE) is None:
                        self.__config[JSTREAMS_PROFILE] = (
                            config.get(JSTREAMS_PROFILE)
                            or config.get(JSTREAMS_PROFILE_LOWER)
                            or config.get(JSTREAMS_PROFILE_CAMEL)
                        )
                    if self.__config.get(JSTREAMS_PACKAGES) is None:
                        self.__config[JSTREAMS_PACKAGES] = (
                            config.get(JSTREAMS_PACKAGES)
                            or config.get(JSTREAMS_PACKAGES_LOWER)
                            or config.get(JSTREAMS_PACKAGES_CAMEL)
                        )

                    if self.__config.get(JSTREAMS_RAISE_BEAN_ERRORS) is None:
                        self.__config[JSTREAMS_RAISE_BEAN_ERRORS] = (
                            config.get(JSTREAMS_RAISE_BEAN_ERRORS)
                            or config.get(JSTREAMS_RAISE_BEAN_ERRORS_LOWER)
                            or config.get(JSTREAMS_RAISE_BEAN_ERRORS_CAMEL)
                        )
                    self.__variables = config.get("variables", {})
            except Exception as e:
                print(e)

    def get_profile(self) -> str | None:
        return self.__config.get(JSTREAMS_PROFILE)

    def get_variable(self, key: str) -> Any | None:
        return self.__variables.get(key)

    def get_packages(self) -> list[str] | None:
        packages: list[str] | None = self.__config.get(JSTREAMS_PACKAGES)
        return packages

    def get_raise_bean_errors(self) -> bool:
        return bool(self.__config.get(JSTREAMS_RAISE_BEAN_ERRORS, False))

    def __get_env_profile(self) -> str | None:
        return (
            os.getenv(JSTREAMS_PROFILE)
            or os.getenv(JSTREAMS_PROFILE_LOWER)
            or os.getenv(JSTREAMS_PROFILE_CAMEL)
        )

    def __get_env_packages(self) -> list[str] | None:
        packages = (
            os.getenv(JSTREAMS_PACKAGES)
            or os.getenv(JSTREAMS_PACKAGES_LOWER)
            or os.getenv(JSTREAMS_PACKAGES_CAMEL)
        )
        if packages is None:
            return None
        return packages.split(",")
