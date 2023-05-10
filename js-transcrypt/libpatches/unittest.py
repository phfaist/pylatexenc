
from pylatexenc.latexnodes import nodes
from pylatexenc import latexnodes

#__pragma__('opov')


# Javascript's maximum stack trace
Error.stack_trace_limit = -1


class _AssertRaisesContext:
    def __init__(self, expected):
        self.expected = expected

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        try:
            exc_name = self.expected.__name__
        except AttributeError:
            exc_name = str(self.expected)

        if exc_type is None:
            raise AssertionError("{} not raised".format(exc_name))

        if not issubclass(exc_type, self.expected):
            # Doesn't work. whatever. at least we have an exception that was raised.
            pass
            #console.log("Raised {}, expected {}".format(exc_type, self.expected))
            #raise AssertionError("Raised {}, expected {}"
            #                     .format(exc_type, self.expected))

        return True # suppress exception.


def _test_equals(a, b):
    print("\t_test_equals()\n\t\t<<< {}\n\t\t>>> {}".format(repr(a),repr(b)))

    if a is None:
        if b is None:
            return True
        return False

    # in the following, `a` is not None.

    if isinstance(a, nodes.LatexNodeList):
        if not _test_equals(a.nodelist, b.nodelist):
            print("\t\tnode list not equal")
            return False
        if not _test_equals(a.pos, b.pos): # _test_equals to handle None
            print("\t\ta.pos[=={}] != b.pos[=={}]".format(a.pos, b.pos))
            return False
        if not _test_equals(a.pos_end, b.pos_end): # _test_equals to handle None
            print("\t\ta.pos_end[=={}] != b.pos_end[=={}]".format(a.pos_end,b.pos_end))
            return False
        return True

    if isinstance(a, (list,tuple)):
        if len(a) != len(b):
            print("\t\tlist lengths differ, {} vs {}".format(len(a),len(b)))
            return False
        for j in range(len(a)):
            x = a[j]
            y = b[j]
            if not _test_equals(x,y):
                print("\t\telement #{} differs:\n\t\t\t<<< {}\n\t\t\t\t!=\n\t\t\t>>> {}"
                      .format(j, x, y))
                return False
        print("\t\tlists are equal")
        return True

    if isinstance(a, set) or isinstance(b, set):
        print("\t\tconverting sets to sorted lists and comparing lists...")
        a = sorted(list(a))
        b = sorted(list(b))
        return _test_equals(a, b)

    if isinstance(a, dict) or isinstance(b, dict):
        a = dict(a)
        b = dict(b)
        print("\t\t[testing keys are the same-- ]")
        res = _test_equals(set(a.keys()), set(b.keys()))
        print("\t\t[testing keys are the same: ", res, "]")
        if not res:
            print("\t\tsets of keys differ")
            return False
        for key in a.keys():
            x = a[key]
            y = b[key]
            if not _test_equals(x, y):
                print("\t\tvalue for key {} differs:\n\t\t\t<<< {}\n\t\t\t\t!=\n\t\t\t>>>  {}"
                      .format(repr(key), repr(x), repr(y)))
                return False
        print("\t\tdicts are equal")
        return True
            

    if isinstance(a, nodes.LatexNode):
        if b is None:
            print("\t\tb is None")
            return False
        if a.nodeType() is not b.nodeType():
            print("\t\tnodeType() mismatch {} != {}".format(repr(a.nodeType()),
                                                            repr(b.nodeType())))
            return False
        if a.parsing_state is not b.parsing_state:
            print("\t\tparsing_state mismatch", a.parsing_state, b.parsing_state)
            return False
        if a.latex_walker is not b.latex_walker:
            print("\t\tlatex_walker mismatch")
            return False
        if not _test_equals(a.pos, b.pos):
            print("\t\tpos mismatch, {} != {}".format(a.pos, b.pos))
            return False
        if not _test_equals(a.pos_end, b.pos_end):
            print("\t\tpos_end mismatch, {} != {}".format(a.pos_end, b.pos_end))
            return False

        for f in a._fields:
            x = getattr(a, f)
            y = getattr(b, f)
            print("\t\ttesting field {}; {} == {} ?".format(f, repr(x), repr(y)))
            if x is None and y is None:
                continue
            if (x is None) != (y is None):
                print("\t\t\tnope, one is None!")
                return False
            if not _test_equals(x, y):
                print("\t\t\tnope!")
                return False
        print("\t\tnodes equal.")
        return True

    if isinstance(a, latexnodes.ParsedArguments):
        if not _test_equals(a.arguments_spec_list, b.arguments_spec_list):
            print("\t\targuments_spec_list differ:\n\t\t\t<<< {}\n\t\t\t\t!=\n\t\t\t>>> {}"
                  .format(repr(a.arguments_spec_list), repr(b.arguments_spec_list)))
            return False
        if not _test_equals(a.argnlist, b.argnlist):
            print("\t\targnlist differ:\n\t\t\t<<< {}\n\t\t\t\t!=\n\t\t\t{}"
                  .format(repr(a.argnlist), repr(b.argnlist)))
            return False
        if not _test_equals(a.pos, b.pos):
            print("\t\tpos differ {} != {}"
                  .format(a.pos, b.pos))
            return False
        if not _test_equals(a.pos_end, b.pos_end):
            print("\t\tpos_end differ {} != {}"
                  .format(a.pos_end, b.pos_end))
            return False
        print("\t\tall ok")
        return True

    # handle __eq__ on our own, it sounds like Transcrypt doesn't try the second
    # object for an __eq__ method ... :/
    if a is not None and a != None and hasattr(a, '__eq__'):
        ok = a.__eq__(b)
    elif b is not None and b != None and hasattr(b, '__eq__'):
        ok = b.__eq__(a)
    else:
        ok = (a == b)
    print("\t\t --> {}".format(ok))
    return ok
    


class TestCase:

    def assertTrue(self, a):
        print("-- bool({}) ?".format(repr(a)))
        assert a

    def assertFalse(self, a):
        print("-- not bool({}) ?".format(repr(a)))
        assert not a

    def assertEqual(self, a, b):
        print("--   {}\n  == {}  ?".format(repr(a),repr(b)))
        assert _test_equals(a, b)

    def assertIs(self, a, b):
        print("-- {} is {} ?".format(repr(a), repr(b)))
        assert a is b

    def assertIsNot(self, a, b):
        print("-- {} is not {} ?".format(repr(a), repr(b)))
        assert a is not b

    def assertIsNone(self, a):
        print("-- {} is None ?".format(repr(a)))
        assert a is None

    def assertIsNotNone(self, a):
        print("-- {} is not None ?".format(repr(a)))
        assert a is not None

    def assertRaises(self, expected):
        print("-- raises {} ?".format(expected.__name__))
        return _AssertRaisesContext(expected)



def do_run_test_modules(test_modules):
    #print("test_objects = ", test_objects)

    test_objects = []

    print("Instantiating tests...")
    my_test_classes = []
    for module in test_modules:
        for membername in dir(module):
            if membername.startswith('Test'):
                cls = getattr(module, membername)
                #print("Class is ", cls.__name__)
                instance = cls()
                #print("Instance is ", instance)
                test_objects.append( {
                    'module': module,
                    'classname': membername,
                    'instance': instance
                } )

    summary_modules = []
    summary_methods = []
    summary_classes = []

    for ti in test_objects:

        tmodule = ti['module']
        tmembername = ti['classname']
        t = ti['instance']

        tmodulename = t.__class__.__module__

        if isinstance(t, TestCase):
            #print("dir(t) = ", dir(t))
            for a in dir(t):
                if a.startswith('test_'):
                    m = getattr(t, a)
                    if callable(m):
                        print(f"*** Run  {tmodulename}.{tmembername}.{a} ***")
                        try:
                            m()
                        except (object) as err:
                            # cf. https://github.com/QQuick/Transcrypt/issues/683#issuecomment-546627982
                            if isinstance(err, BaseException):
                                excname = err.__class__.__name__
                                msg = f"[PY] {excname}: {repr(err.__args__)}"
                                err2 = Error(f'EXCEPTION - {excname} - {repr(err.__args__)}')
                            else:
                                err2 = err
                                msg = str(err)
                            tb = err.stack or '(stack trace not available)'
                            print(f"""

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                              ❗❗❗ ERROR ❗❗❗
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

❗❗❗ In {t.__class__.__module__}::{t.__class__.__name__}::{a} ❗❗❗

{msg}

Traceback:
{tb}

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                                     ❗❗❗
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
""")
                            raise err2
                        print(f"*** Done {tmodulename}.{tmembername}.{a} ***")
                        summary_methods.append(
                            f"{t.__class__.__module__}::{t.__class__.__name__}::{a} ✓"
                        )
            summary_classes.append(
                f"{t.__class__.__module__}::{t.__class__.__name__} ✓"
            )
        summary_modules.append(
            f"{t.__class__.__module__} ✓"
        )


    # print summary
    print(r"""

********************************************************************************
                                    SUMMARY
********************************************************************************

METHODS:
--------

{}


CLASSES:
--------

{}


MODULES:
--------

{}

""".format(
    "\n".join([ '+ '+x for x in summary_methods]),
    "\n".join([ '+ '+x for x in summary_classes]),
    "\n".join([ '+ '+x for x in summary_modules]),
    ))
