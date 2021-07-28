from typing import Optional

from wpsync.log import AbstractLogger, TermLogger


class WPSync:
    def __init__(
        self,
        logger: Optional[AbstractLogger] = None,
        log_level: Optional[int] = None,
        config: Optional[str] = None,
    ):
        if logger:
            if log_level is not None:
                raise ValueError(
                    "doesn't make sense to specify a log_level and supply a custom logger at the same time"
                )
            self.logger = logger
        else:
            if log_level is not None:
                self.logger = TermLogger(level=log_level)
            else:
                self.logger = TermLogger()
        if config is not None:
            # TODO load config from given location
            pass
        else:
            # TODO load config from standard location
            pass

    def sync(
        self,
        # TODO use proper config object here?
        source: str,
        target: str,
        # TODO could fewer options express everything, too, but
        # more succinctly?
        database: Optional[bool] = None,
        uploads: Optional[bool] = None,
        plugins: Optional[bool] = None,
        themes: Optional[bool] = None,
        all: Optional[bool] = None,
        full: Optional[bool] = None,
    ):
        raise NotImplementedError()

    def backup(self):
        raise NotImplementedError()

    def restore(self):
        raise NotImplementedError()

    def list(self):
        raise NotImplementedError()

    def install(self):
        raise NotImplementedError()
