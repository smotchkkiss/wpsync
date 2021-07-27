__version__ = "2.0.1"

from typing import Optional

from wpsync.wpsync import WPSync


def sync(*args, **kwargs):
    wpsync = _get_default_instance()
    return wpsync.sync(*args, **kwargs)


def backup(*args, **kwargs):
    wpsync = _get_default_instance()
    return wpsync.backup(*args, **kwargs)


def restore(*args, **kwargs):
    wpsync = _get_default_instance()
    return wpsync.restore(*args, **kwargs)


def list(*args, **kwargs):
    wpsync = _get_default_instance()
    return wpsync.list(*args, **kwargs)


def install(*args, **kwargs):
    wpsync = _get_default_instance()
    return wpsync.install(*args, **kwargs)


_default_instance: Optional[WPSync] = None


def _get_default_instance():
    global _default_instance
    if not _default_instance:
        _default_instance = WPSync()
    return _default_instance
