class WPSync:
    def __init__(self, logger=None):
        if logger:
            self.logger = logger
        else:
            # TODO create instance of default logger class
            self.logger = None

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
