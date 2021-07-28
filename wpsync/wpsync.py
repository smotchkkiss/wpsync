from wpsync.log import TermLogger


class WPSync:
    def __init__(self, logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = TermLogger()

    def sync(self):
        raise NotImplementedError()

    def backup(self):
        raise NotImplementedError()

    def restore(self):
        raise NotImplementedError()

    def list(self):
        raise NotImplementedError()

    def install(self):
        raise NotImplementedError()
