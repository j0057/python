
def color(*c):
    return '\x1B[{0}m'.format(';'.join(map(str, c))) if color.ENABLED else ''

map(lambda (k, v): setattr(color, k, v), dict(DEFAULT=0, BOLD=1, 
    FG_BLACK=30, FG_RED=31, FG_GREEN=32, FG_BROWN=33, FG_BLUE=34, FG_MAGENTA=35, FG_CYAN=36, FG_WHITE=37, 
    BG_BLACK=40, BG_RED=41, BG_GREEN=42, BG_BROWN=43, BG_BLUE=44, BG_MAGENTA=45, BG_CYAN=46, BG_WHITE=47,
    ENABLED=True).items())	

class BaseDec(object):
    def __init__(self, func):
        self.func = func
        self.__name__ = self.func.__name__
    def __get__(self, object, type=None):
        if type is None:
            return self
        new_func = self.func.__get__(object, type)
        return self.__class__(new_func)

def returns(value):
    class returns_dec(BaseDec):
        is_test = True
        def __call__(self, *a, **k):
            try:
                result = self.func(*a, **k)
                assert result == value, \
                    'result: {0}; expected result: {1}'.format(result, value)
                return result
            except AssertionError:
                raise
            except Exception as ex:
                assert False, \
                    'raises: {0} ({1}); expected result: {2}'.format(type(ex).__name__, str(ex), value)    
    return returns_dec

def raises(exception_type):
    class raises_dec(BaseDec):
        is_test = True
        def __call__(self, *a, **k):
            try:
                result = self.func(*a, **k)
                assert False, \
                    'result: {0}; expected exception: {1}'.format(result, exception_type.__name__)
            except AssertionError:
                raise
            except Exception as ex:
                assert type(ex) == exception_type, \
                    'raises: {0} ({1}); expected exception: {2}'.format(type(ex).__name__, str(ex), exception_type.__name__)
                return ex
    return raises_dec

class BaseTest(object):
    @staticmethod
    def run_all_tests(base_class, g=None):
        if g is None: g = globals()
        BaseTest.run_tests(*[ obj
            for obj in g.itervalues()
            if isinstance(obj, type)
            if base_class in obj.__bases__ ])

    @staticmethod
    def run_tests(*classes):
        tests_ok, tests_fail, tests_ran, failed = 0, 0, 0, []
        for class_ in classes:
            print color(color.FG_BROWN, color.BOLD) + class_.__name__ + color(color.DEFAULT)
            ok, fail, ran = class_().run()
            print '{5}{0}{4} -- {6}ok: {1}/{3}; failed: {2}/{3}{4}'.format(
                class_.__name__,
                ok, fail, ran,
                color(color.DEFAULT),
                color(color.FG_BROWN, color.BOLD),
                color(color.FG_GREEN if ok == ran else color.FG_RED, color.BOLD))
            tests_ok += ok
            tests_fail += fail
            tests_ran += ran
            if fail:
                failed += [class_.__name__]
            print
        print 'ok: {0}/{2}; fail: {1}/{2}; failing: {3}'.format(
            tests_ok,
            tests_fail,
            tests_ran,
            ', '.join(failed))

    def run(self):
        methods = [ getattr(self, name)
            for name in sorted(dir(self))
            if callable(getattr(self, name)) 
            if hasattr(getattr(self, name), 'is_test') ]
        tests_ok = 0
        tests_fail = 0
        tests_total = len(methods)
        for method in methods:
            try:
                result = method()
                print '  ' + color(color.FG_GREEN, color.BOLD) + method.__name__ + color(color.DEFAULT) \
                    + ' ' + repr(result)
                tests_ok += 1
            except Exception as ex:
                print '  ' + color(color.FG_RED, color.BOLD) + method.__name__ + color(color.DEFAULT) \
                    + ' ' + repr(ex)
                tests_fail += 1
        return tests_ok, tests_fail, tests_total            
