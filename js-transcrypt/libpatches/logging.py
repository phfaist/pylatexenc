#
# mini-patch logger
#

class MinimalLogger:
    def _emit(self, m, args):
        s = "{}{}".format(m, args[0])
        if len(args) > 1:
            s += "  //  "
            s += " ; ".join([repr(a) for a in args[1:]])
        print(s)

    def error(self, *args):
        self._emit("[[logging.ERROR!!]]  ", args)

    def critical(self, *args):
        self._emit("[[logging.CRITICAL!!]]  ", args)

    def warning(self, *args):
        self._emit("[[logging.WARNING!]]  ", args)

    def info(self, *args):
        self._emit("", args)

    def debug(self, *args):
        self._emit("logging.debug -- ", args)


single_logger_instance = MinimalLogger()

def getLogger(*args, **kwargs):
    return single_logger_instance


def basicConfig(*args, **kwargs):
    pass
