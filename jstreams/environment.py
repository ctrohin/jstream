import os
from typing import Any, Final, Optional
from json import load

JSTREAMS_PROFILE: Final[str] = "JSTREAMS_PROFILE"
JSTREAMS_PACKAGES: Final[str] = "JSTREAMS_PACKAGES"


class JStreamsEnv:
    """
    Class that holds all the environment variables used by JStreams
    """

    __slots__ = "__config"

    def __init__(self) -> None:
        self.__config: dict[str, Any] = {}
        self.__load_config()

    def __load_config(self) -> None:
        if profile := self.__get_env_profile() is not None:
            self.__config[JSTREAMS_PROFILE] = profile
        if packages := self.__get_env_packages() is not None:
            self.__config[JSTREAMS_PACKAGES] = packages

        if os.path.exists("jstreams.json"):
            try:
                config = load(open("jstreams.json"))
                if self.__config.get(JSTREAMS_PROFILE) is None:
                    self.__config[JSTREAMS_PROFILE] = config.get(JSTREAMS_PROFILE)
                if self.__config.get(JSTREAMS_PACKAGES) is None:
                    self.__config[JSTREAMS_PACKAGES] = config.get(JSTREAMS_PACKAGES)
            except Exception as e:
                print(e)

    def get_profile(self) -> Optional[str]:
        return self.__config.get(JSTREAMS_PROFILE)

    def get_packages(self) -> list[str]:
        return self.__config.get(JSTREAMS_PACKAGES)

    def __get_env_profile(self) -> Optional[str]:
        return os.getenv(JSTREAMS_PROFILE)

    def __get_env_packages(self) -> Optional[list[str]]:
        packages = os.getenv(JSTREAMS_PACKAGES)
        if packages is None:
            return None
        return packages.split(",")
