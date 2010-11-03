#!/usr/bin/python

import itertools

class Query_Base(object):
    def __init__(self, iterable):
        self.iterable = iterable
    def __iter__(self):
        return iter(self.iterable)    
    
class Query_Restriction(Query_Base):
    def where(self, pred):
        return self.__class__(item for item in self if pred(item))

class Query_Projection(Query_Base):
    def select(self, func):
        return self.__class__(func(item) for item in self)
    def selectmany(self, seq_selector, result_selector=None):
        def selectmany_gen(seq_selector, result_selector):
            for sub_seq in self:
                for item in seq_selector(sub_seq):
                    if result_selector:
                        yield result_selector(item)
                    else:
                        yield item
        return self.__class__(selectmany_gen(seq_selector, result_selector))

class Query_Partitioning(Query_Base):
    def take(self, count):
        def take_gen(count):
            i = iter(self)
            while count:
                yield i.next()
                count -= 1
        return self.__class__(take_gen(count))
    def skip(self, count):
        def skip_gen(count):
            i = iter(self)
            while count:
                i.next()
                count -= 1
            while True:
                yield i.next()
        return self.__class__(skip_gen(count))
    def takewhile(self, pred):
        def takewhile_gen(pred):
            i = iter(self)
            while True:
                item = i.next()
                if not pred(item):
                    break
                yield item
        return self.__class__(takewhile_gen(pred))
    def skipwhile(self, pred):
        def skipwhile_gen(pred):
            i = iter(self)
            while True:
                item = i.next()
                if not pred(item):
                    yield item
                    break
            while True:
                yield i.next()
        return self.__class__(skipwhile_gen(pred))

class Query_Ordering(Query_Base):
    def orderby(self, key_selector=None):
        def orderby_gen():
            for item in sorted(self, key=key_selector):
                yield item
        return self.__class__(orderby_gen())
    thenby = orderby

class Query_Grouping(Query_Base):
    def groupby(self, key_selector=None, val_selector=None):
        result = {} # this is greedy...but there's no other way to do it other than returning the same key
                    # multiple times.
        key_selector = key_selector or (lambda item: item)
        val_selector = val_selector or (lambda item: item)
        for k, v in self.select(lambda item: (key_selector(item), val_selector(item))):
            try:
                result[k].append(v)
            except KeyError:
                result[k] = [v]
        return self.__class__((k, self.__class__(v)) for (k, v) in result.iteritems())

class Query_Sets(Query_Base):
    def distinct(self):
        def distinct_gen():
            seen = set()
            for item in self:
                if item in seen:
                    continue
                seen |= set([item])
                yield item
        return self.__class__(distinct_gen())
    def union(self, other):
        def union_gen():
            seen = set([])
            for item in self:
                if item not in seen:
                    yield item
                    seen |= set([item])
            for item in other:
                if item not in seen:
                    yield item
                    seen |= set([item])            
        return self.__class__(union_gen())
    def intersect(self, other):
        def intersect_gen():
            s2 = set(other)
            for item in self:
                if item in s2:
                    yield item
        return self.__class__(intersect_gen())
    def difference(self, other):
        def difference_gen():
            s2 = set(other)
            for item in self:
                if item in s2:
                    continue
                yield item
        return self.__class__(difference_gen())

class Query_Conversion(Query_Base):
    def tolist(self):
        return list(self)
    def todict(self, proj1=None, proj2=None):
        if proj1 and proj2:
            return self \
                .select(lambda item: (proj1(item), proj2(item))) \
                .todict()
        elif proj1:
            return self \
                .select(lambda item: (item, proj1(item))) \
                .todict()
        else:
            return dict(self)

class Query_Elements(Query_Base):
    def first(self, pred=None):
        if pred:
            return self.where(pred).first()
        else:
            i = iter(self)
            try:
                return i.next()
            except StopIteration:
                raise ValueError('Empty sequence')
    def firstordefault(self, pred=None, default=None):
        try:
            return self.first(pred)
        except ValueError:
            return default
    def last(self, pred=None):
        if pred:
            return self.where(pred).last()
        else:
            item = no_item = object()
            for item in self:
                pass
            if item != no_item:
                return item
            else:
                raise ValueError('Empty sequence')
    def lastordefault(self, pred=None, default=None):
        try:
            return self.last(pred)
        except ValueError:
            return default
    def single(self, pred=None):
        if pred:
            return self.where(pred).single()
        else:
            i = iter(self)
            try:
                result = i.next()
            except StopIteration:
                raise ValueError('Empty sequence')
            try:
                i.next()
                raise ValueError('Sequence contains more than one item')
            except StopIteration:
                return result
    def singleordefault(self, pred=None, default=None):
        if pred:
            return self.where(pred).singleordefault(default=default)
        else:
            result = no_result = object()
            i = iter(self)
            try:
                result = i.next()
            except StopIteration:
                return default
            try:
                i.next()
                raise ValueError('Sequence contains more than one item')
            except StopIteration:
                return result
    def elementat(self, index):
        for idx, item in enumerate(self):
            if idx == index:
                return item
        raise IndexError('No item with index {0}'.format(index))
    
class Query_Generation(Query_Base):
    pass

class Query_Quantifiers(Query_Base):
    def any(self, pred=None):
        if pred:
            return self.select(pred).any()
        else:
            for item in self:
                if item:
                    return True
            return False
    def all(self, pred=None):
        if pred:
            return self.select(pred).all()
        else:
            for item in self:
                if not item:
                    return False
            return True

class Query_Aggregates(Query_Base):
    def aggregate(self, func, initial=None, allow_empty=True):
        result = initial
        is_empty = True
        for item in self:
            is_empty = False
            result = func(result, item)
        if is_empty and not allow_empty:
            raise ValueError('Empty sequence')
        return result
    def sum(self, selector=None):
        if selector:
            return self.select(selector).sum()
        else:
            return self.aggregate(lambda a, b: a + b, initial=0, allow_empty=False)
    def average(self, selector=None):
        if selector:
            return self.select(selector).average()
        else:
            i1, i2 = itertools.tee(self)
            return float(self.__class__(i1).sum()) / self.__class__(i2).count()
    def min(self, pred=None):
        if pred:
            return self.where(pred).min()
        else:
            lowest = self.first()
            for item in self.skip(1):
                if item < lowest:
                    lowest = item
            return lowest
    def max(self, pred=None):
        if pred:
            return self.where(pred).max()
        else:
            highest = self.first()
            for item in self.skip(1):
                if item > highest:
                    highest = item
            return highest
    def count(self, pred=None):
        if pred:
            return self.where(pred).count()
        else:
            count = 0
            for item in self:
                count += 1
            return count

class Query_Misc(Query_Base):
    pass

class Query_Joins(Query_Base):
    pass
        
class Query(Query_Restriction, Query_Projection, Query_Partitioning, Query_Ordering, Query_Grouping, Query_Sets, 
        Query_Conversion, Query_Elements, Query_Generation, Query_Quantifiers, Query_Aggregates, Query_Misc, 
        Query_Joins):
    pass
        
Q = Query

if __name__ == '__main__':
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
                print class_.__name__
                ok, fail, ran = class_().run()
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
                #if name.startswith('test_')
                if callable(getattr(self, name)) 
                if hasattr(getattr(self, name), 'is_test') ]
            tests_ok = 0
            tests_fail = 0
            tests_total = len(methods)
            for method in methods:
                print '  ', method.__name__,
                try:
                    result = method()
                    print
                    tests_ok += 1
                except Exception as ex:
                    print ex
                    tests_fail += 1
            print '{0} -- ok: {1}/{3}; failed: {2}/{3}'.format(
                type(self).__name__, tests_ok, tests_fail, tests_total)
            return tests_ok, tests_fail, tests_total            
        
    class Test(BaseTest):
        def __init__(self):
            self.L  = [1,2,3,4,5,6,7,8,9,10]
            self.M  = [4,5,6]
            self.E  = []
            self.D  = [1.1, 1.2, 3.1, 3.2, 3.3, 3.4, 3.5]
            self.W1 = ['The quick brown', 'fox jumps over', 'the lazy dogs']
            self.W2 = [['The', 'quick', 'brown'], ['fox', 'jumps', 'over'], ['the', 'lazy', 'dogs']]
            self.G  = ['blueberry', 'chimpanzee', 'abacus', 'banana', 'apple', 'cheese']
            self.R1 = [6,10,5,2,8,9,4,1,3,7]
            self.R2 = [(1,6),(2,10),(3,5),(2,5),(2,9),(1,9),(1,4),(2,1),(3,3),(7,3)]
            self.S1 = [0,2,4,5,6,8,9]
            self.S2 = [1,3,5,7,8]

    class TestRestriction(Test):
        @returns([2, 4, 6, 8, 10])
        def where(self):
            return Query(self.L).where(lambda n: n % 2 == 0).tolist()

    class TestProjection(Test):
        @returns([2, 4, 6, 8, 10, 12, 14, 16, 18, 20])
        def select(self):
            return Query(self.L).select(lambda n: n * 2).tolist()
        @returns(['The', 'quick', 'brown', 'fox', 'jumps', 'over', 'the', 'lazy', 'dogs'])
        def selectmany_1(self):
            return Query(self.W1) \
                .selectmany(lambda s: s.split(' ')) \
                .tolist()
        @returns(['he', 'uick', 'rown', 'ox', 'umps', 'ver', 'he', 'azy', 'ogs'])
        def selectmany_2(self):
            return Query(self.W1) \
                .selectmany(lambda s: s.split(' '), lambda s: s[1:]) \
                .tolist()
        @returns(['The', 'quick', 'brown', 'fox', 'jumps', 'over', 'the', 'lazy', 'dogs'])
        def selectmany_3(self):
            return Query(self.W2) \
                .selectmany(lambda sx: sx) \
                .tolist()
        @returns(['The', 'quick', 'brown', 'fox', 'jumps', 'over', 'the', 'lazy', 'dogs'])
        def selectmany_4(self):
            return Query(self.W1) \
                .select(lambda s: s.split(' ')) \
                .selectmany() \
                .tolist()

    class TestPartitioning(Test):
        @returns([1, 2, 3])
        def take(self):
            return Query(self.L).take(3).tolist()
        @returns([8, 9, 10])
        def skip(self):
            return Query(self.L).skip(7).tolist()
        @returns([1, 2, 3])
        def takewhile(self):
            return Query(self.L).takewhile(lambda n: n < 4).tolist()
        @returns([8, 9, 10])
        def skipwhile(self):
            return Query(self.L).skipwhile(lambda n: n < 8).tolist()

    class TestOrdering(Test):
        @returns([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        def orderby_1(self):
            return Query(self.R1) \
                .orderby() \
                .tolist()
        @returns([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        def orderby_2(self):
            return Query(self.R1) \
                .orderby(lambda n: n) \
                .tolist()
        @returns([])
        def thenby_1(self):
            return Query(self.R2) \
                .orderby(lambda n: n[0]) \
                .thenby(lambda n: n[1]) \
                .tolist()

    class TestGrouping(Test):
        @returns({'b':['blueberry', 'banana'], 'c':['chimpanzee', 'cheese'], 'a':['abacus', 'apple']})
        def groupby(self):
            return Query(self.G) \
                .groupby(lambda s: s[0]) \
                .select(lambda (key, items): (key, items.tolist())) \
                .todict()

    class TestSets(Test):
        @returns([2,3,5])
        def distinct(self):
            return Query([2,2,3,5,5]) \
                .distinct() \
                .tolist()
        @returns([0,2,4,5,6,8,9,1,3,7])
        def union(self):
            return Query(self.S1) \
                .union(Query(self.S2)) \
                .tolist()
        @returns([5,8])
        def interect(self):
            return Query(self.S1) \
                .intersect(Query(self.S2)) \
                .tolist()
        @returns([0,2,4,6,9])
        def difference(self):
            return Query(self.S1) \
                .difference(Query(self.S2)) \
                .tolist()

    class TestConversion(Test):
        @returns({1:2, 2:4, 3:6, 4:8})
        def todict_1(self):
            return Query(self.L) \
                .where(lambda n: n <= 4) \
                .select(lambda n: (n, 2*n)) \
                .todict()
        @returns({1:2, 2:4, 3:6, 4:8})
        def todict_2(self):
            return Query(self.L) \
                .where(lambda n: n <= 4) \
                .todict(lambda n: 2 * n)
        @returns({2:3, 4:6, 6:9, 8:12})
        def todict_3(self):
            return Query(self.L) \
                .where(lambda n: n <= 4) \
                .todict(lambda n: 2 * n, lambda n: 3 * n)

    class TestElement(Test):
        @returns(1)
        def elementat_1(self):
            return Query(self.L).elementat(0)
        @returns(10)
        def elementat_2(self):
            return Query(self.L).elementat(9)
        @returns(1)
        def first_1a(self):
            return Query(self.L).first()
        @raises(ValueError)
        def first_1b(self):
            return Query(self.E).first()
        @returns(3.1)
        def first_2a(self):
            return Query(self.D).first(lambda n: 3 <= n <= 4)
        @raises(ValueError)
        def first_2b(self):
            return Query(self.E).first(lambda n: 3 <= n <= 4)
        @returns(10)
        def last_1a(self):
            return Query(self.L).last()
        @raises(ValueError)
        def last_1b(self):
            return Query(self.E).last()
        @returns(3.5)
        def last_2a(self):
            return Query(self.D).last(lambda n: 3 <= n <= 4)
        @raises(ValueError)
        def last_2b(self):
            return Query(self.E).last(lambda n: 3 <= n <= 4)
        @returns(1)
        def firstordefault_1(self):
            return Query(self.L).firstordefault()
        @returns(42)
        def firstordefault_2(self):
            return Query(self.E).firstordefault(default=42)
        @returns(4)
        def single_1a(self):
            return Query(self.L).where(lambda n: n == 4).single()
        @raises(ValueError)
        def single_1b(self):
            return Query(self.L).where(lambda n: n < 4).single()
        @raises(ValueError)
        def single_1c(self):
            return Query(self.L).where(lambda n: n >= 4).single()
        @returns(4)
        def single_2a(self):
            return Query(self.L).single(lambda n: n == 4)
        @raises(ValueError)
        def single_2b(self):
            return Query(self.L).single(lambda n: n < 4)
        @raises(ValueError)
        def single_2c(self):
            return Query(self.L).single(lambda n: n >= 4)
        @returns(4)
        def singleordefault_1a(self):
            return Query(self.L).where(lambda n: n == 4).singleordefault(default=42)
        @returns(42)
        def singleordefault_1b(self):
            return Query(self.L).where(lambda n: n > 10).singleordefault(default=42)
        @raises(ValueError)
        def singleordefault_1c(self):
            return Query(self.L).where(lambda n: n < 4).singleordefault(default=42)
        @raises(ValueError)
        def singleordefault_1d(self):
            return Query(self.L).where(lambda n: n >= 4).singleordefault(default=42)
        @returns(4)
        def singleordefault_2a(self):
            return Query(self.L).singleordefault(lambda n: n == 4, default=42)
        @returns(42)
        def singleordefault_2b(self):
            return Query(self.L).singleordefault(lambda n: n > 10, default=42)
        @raises(ValueError)
        def singleordefault_2c(self):
            return Query(self.L).singleordefault(lambda n: n < 4, default=42)
        @raises(ValueError)
        def singleordefault_2d(self):
            return Query(self.L).singleordefault(lambda n: n >= 4, default=42)

    class TestGeneration(Test):
        @returns(None)
        def dummy(self):
            pass

    class TestQuantifiers(Test):
        @returns(True)
        def any_1a(self):
            return Query([False, False, True]).any()
        @returns(False)
        def any_1b(self):
            return Query([False, False, False]).any()
        @returns(True)
        def any_2a(self):
            return Query(self.L).any(lambda n: n <= 1)
        @returns(False)
        def any_2b(self):
            return Query(self.L).any(lambda n: n < 1)
        @returns(True)
        def all_1a(self):
            return Query([True, True, True]).all()
        @returns(False)
        def all_1b(self):
            return Query([True, True, False]).all()
        @returns(True)
        def all_2a(self):
            return Query(self.L).all(lambda n: n > 0)
        @returns(False)
        def all_2b(self):
            return Query(self.L).all(lambda n: n > 1)
        @returns(True)
        def contains_1(self):
            return Query(self.L).contains(1)
        @returns(False)
        def contains_2(self):
            return Query(self.L).contains(0)

    class TestAggregates(Test):
        @returns(55)
        def aggregate_1(self):
            return Query(self.L).aggregate(lambda a,b: a + b, initial=0)
        @returns(3628800)
        def aggregate_2(self):
            return Query(self.L).aggregate(lambda a,b: a * b, initial=1)
        @raises(TypeError)
        def aggregate_3(self):
            return Query(self.L).aggregate(lambda a,b: a + b)
        @returns(55)
        def sum_1a(self):
            return Query(self.L).sum()
        @raises(ValueError)
        def sum_1b(self):
            return Query(self.E).sum()
        @returns(110)
        def sum_2a(self):
            return Query(self.L).sum(lambda n: 2 * n)
        @raises(ValueError)
        def sum_2b(self):
            return Query(self.E).sum(lambda n: 2 * n)
        @returns(5.5)
        def average_1a(self):
            return Query(self.L).average()
        @raises(ValueError)
        def average_1b(self):
            return Query(self.E).average()
        @returns(11)
        def average_2a(self):
            return Query(self.L).average(lambda n: 2 * n)
        @raises(ValueError)
        def average_2b(self):
            return Query(self.E).average(lambda n: 2 * n)
        @returns(1)
        def min_1a(self):
            return Query(self.L).min()
        @raises(ValueError)
        def min_1b(self):
            return Query(self.E).min()
        @returns(5)
        def min_2a(self):
            return Query(self.L).min(lambda n: n >= 5)
        @raises(ValueError)
        def min_2b(self):
            return Query(self.E).min(lambda n: n >= 5)
        @returns(10)
        def max_1a(self):
            return Query(self.L).max()
        @raises(ValueError)
        def max_1b(self):
            return Query(self.E).max()
        @returns(5)
        def max_2a(self):
            return Query(self.L).max(lambda n: n <= 5)
        @raises(ValueError)
        def max_2b(self):
            return Query(self.E).max(lambda n: n <= 5)
        @returns(5)
        def count_1a(self):
            return Query(self.L).where(lambda n: n <= 5).count()
        @returns(0)
        def count_1b(self):
            return Query(self.L).where(lambda n: n > 10).count()
        @returns(5)
        def count_2a(self):
            return Query(self.L).count(lambda n: n <= 5)
        @returns(0)
        def count_2b(self):
            return Query(self.L).count(lambda n: n > 10)

    class TestJoins(Test):
        @returns([('AA', 'AB'), ('BA', 'BB'), ('CA', 'CB')])
        def join(self):
            return Query(['AA', 'BA', 'CA']) \
                .join(['AB', 'BB', 'CB'], lambda a: a[0], lambda b: b[0], lambda a, b: (a,b)) \
                .tolist()

    class TestMisc(Test):
        @returns(1)
        def elementatordefault_1(self):
            return Query(self.L).elementatordefault(1, default=42)
        @returns(42)
        def elementatordefault_2(self):
            return Query(self.L).elementatordefault(0, default=42)
        @returns([1,2,3,4,5,6,7,8,9,10])
        def defaultifempty_1(self):
            return Query(self.L).defaultifempty(default=[42]).tolist()
        @returns([42])
        def defaultifempty_2(self):
            return Query(self.E).defaultifempty(default=[42]).tolist()
        @returns(["Foo", "Bar"])
        def oftype(self):
            return Query([1, "Foo", 2, "Bar"]).oftype(str).tolist()
        @returns([10,9,8,7,6,5,4,3,2,1])
        def reversed(self):
            return Query(self.L).reversed().tolist()
        @returns([1,2,3,4,5,6])
        def concat(self):
            return Query([1,2,3]).concat([4,5,6]).tolist()
        @returns([(1,3),(2,4),(3,5)])
        def zip(self):
            return Query([1,2,3]).zip([4,5,6], lambda a,b: (a,b))
        @returns([6,6,6])
        def repeat(self):
            return Query.repeat(6).take(3).tolist()
        @returns(True)
        def sequenceequal(self):
            return Query(self.L).sequenceequal(self.L)



    BaseTest.run_all_tests(base_class=Test, g=globals())
