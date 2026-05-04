import os
from typing import Any, Final
from json import load
from collections.abc import Mapping

JSTREAMS_PROFILE: Final[str] = "JSTREAMS_PROFILE"
JSTREAMS_PROFILE_LOWER: Final[str] = "jstreams_profile"
JSTREAMS_PROFILE_CAMEL: Final[str] = "jstreamsProfile"

JSTREAMS_PROFILE_ARR: Final[list[str]] = [
    JSTREAMS_PROFILE,
    JSTREAMS_PROFILE_LOWER,
    JSTREAMS_PROFILE_CAMEL,
]

JSTREAMS_PACKAGES: Final[str] = "JSTREAMS_PACKAGES"
JSTREAMS_PACKAGES_LOWER: Final[str] = "jstreams_packages"
JSTREAMS_PACKAGES_CAMEL: Final[str] = "jstreamsPackages"

JSTREAMS_PACKAGES_ARR: Final[list[str]] = [
    JSTREAMS_PACKAGES,
    JSTREAMS_PACKAGES_LOWER,
    JSTREAMS_PACKAGES_CAMEL,
]


JSTREAMS_CONFIG_JSON: Final[str] = "JSTREAMS_CONFIG_JSON"
DEFAULT_FILE: Final[str] = "jstreams.json"

JSTREAMS_RAISE_BEAN_ERRORS: Final[str] = "JSTREAMS_RAISE_BEAN_ERRORS"
JSTREAMS_RAISE_BEAN_ERRORS_LOWER: Final[str] = "jstreams_raise_bean_errors"
JSTREAMS_RAISE_BEAN_ERRORS_CAMEL: Final[str] = "jstreamsRaiseBanErrors"

JSTREAMS_RAISE_BEAN_ERRORS_ARR: Final[list[str]] = [
    JSTREAMS_RAISE_BEAN_ERRORS,
    JSTREAMS_RAISE_BEAN_ERRORS_LOWER,
    JSTREAMS_RAISE_BEAN_ERRORS_CAMEL,
]


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
                        self.__config[JSTREAMS_PROFILE] = self.__first_non_null(
                            config, JSTREAMS_PROFILE_ARR
                        )
                    if self.__config.get(JSTREAMS_PACKAGES) is None:
                        self.__config[JSTREAMS_PACKAGES] = self.__first_non_null(
                            config, JSTREAMS_PACKAGES_ARR
                        )

                    if self.__config.get(JSTREAMS_RAISE_BEAN_ERRORS) is None:
                        self.__config[JSTREAMS_RAISE_BEAN_ERRORS] = (
                            self.__first_non_null(
                                config, JSTREAMS_RAISE_BEAN_ERRORS_ARR
                            )
                        )
                    self.__process_variables(config.get("values", {}))
            except Exception as e:
                print(e)

    def __process_variables(self, variables: dict[str, Any]) -> None:
        self.__variables = {}
        for key, value in variables.items():
            if isinstance(value, dict):
                self.__process_dict_vars(key, value)
            else:
                self.__variables[key] = value

    def __process_dict_vars(self, prefix: str, variables: dict[str, Any]) -> None:
        for key, value in variables.items():
            if isinstance(value, dict):
                self.__process_dict_vars(f"{prefix}.{key}", value)
            else:
                self.__variables[f"{prefix}.{key}"] = value

    def get_profile(self) -> str | None:
        return self.__config.get(JSTREAMS_PROFILE)

    def get_variable(self, key: str) -> Any | None:
        if (var := self.__variables.get(key)) is not None:
            return var
        return os.getenv(key)

    def get_packages(self) -> list[str] | None:
        packages: list[str] | None = self.__config.get(JSTREAMS_PACKAGES)
        return packages

    def get_raise_bean_errors(self) -> bool:
        return bool(self.__config.get(JSTREAMS_RAISE_BEAN_ERRORS, False))

    def __get_env_profile(self) -> str | None:
        return self.__first_env_non_null(JSTREAMS_PROFILE_ARR)

    def __get_env_packages(self) -> list[str] | None:
        if packages := self.__first_env_non_null(JSTREAMS_PACKAGES_ARR):
            return packages.split(",")
        return None

    def __first_env_non_null(self, keys: list[str]) -> str | None:
        return self.__first_non_null(os.environ, keys)

    def __first_non_null(self, dct: Mapping[str, Any], keys: list[str]) -> Any | None:
        for key in keys:
            if (value := dct.get(key)) is not None:
                return value
        return None
