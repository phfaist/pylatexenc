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
        self._emit("ERROR !!  ", args)

    def critical(self, *args):
        self._emit("CRITICAL !!  ", args)

    def warning(self, *args):
        self._emit("WARNING !  ", args)

    def info(self, *args):
        self._emit("", args)

    def debug(self, *args):
        self._emit("debug --- ", args)


def getLogger(*args, **kwargs):
    return MinimalLogger()



def basicConfig(*args, **kwargs):
    pass
