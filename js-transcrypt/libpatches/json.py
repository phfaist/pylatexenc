
def loads(s, object_hook=None):
    if not object_hook:
        return JSON.parse(s)
    __pragma__('js', "{}", """
    var wrap_object_hook = (value) => {
       if (value instanceof Array || value instanceof Number || value instanceof String) {
           return value;
       }
       return object_hook(value);
    };""")
    return JSON.parse(s, wrap_object_hook)


def dumps(d, indent=0):
    return JSON.stringify(d, None, indent)


def dump(d, f, indent=0):
    f.write(dumps(d, indent))


