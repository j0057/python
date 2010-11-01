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
	pass

class Query_Grouping(Query_Base):
	#def groupby(self, key_selector=None):
	#	def groupby_gen(key_selector):
	#		for (key, values) in itertools.groupby(self, key_selector):
	#			yield (key, self.__class__(values))
	#	return self.__class__(groupby_gen(key_selector))
	
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
	pass

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
	pass

class Query_Aggregates(Query_Base):
	def aggregate(self, func, initial=None):
		result = initial
		for item in self:
			result = func(result, item)
		return result
	
	def sum(self):
		return self.aggregate(lambda a, b: a + b)
		
	def average(self):
		return float(self.sum()) / self.count()
	
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
	def returns(value):
		def returns_dec(func):
			def returns_func():
				try:
					result = func()
					assert result == value, \
						'result: {0}; expected result: {1}'.format(result, value)
				except AssertionError:
					raise
				except Exception as ex:
					assert False, \
						'raises: {0} - {1}; expected result: {2}'.format(type(ex).__name__, str(ex), value)
			returns_func.__name__ = func.__name__
			return returns_func
		return returns_dec

	def raises(exception_type):
		def raises_dec(func):
			#functools.decorator(func)
			def raises_func():
				try:
					result = func()
					assert False, \
						'result: {0}; expected exception: {1}'.format(result, exception_type)
				except AssertionError:
					raise
				except Exception as ex:
					assert type(ex) == exception_type, \
						'raises: {0} - {1}; expected exception: {2}'.format(type(ex).__name__, str(ex), exception_type)
			raises_func.__name__ = func.__name__
			return raises_func
		return raises_dec

	def run_tests(functions=None, test_prefix='test_'):
		if functions is None:
			g = globals()
			functions = [ g[name]
				for name in sorted(globals().keys())
				if name.startswith(test_prefix) 
				if callable(g[name]) ]
		tests_ok = 0
		tests_fail = 0
		for function in functions:
			print function.__name__,
			try:
				result = function()
				print
				tests_ok += 1
			except Exception as ex:
				print ex
				tests_fail += 1
		print 'ok: {0}/{2}; failed: {1}/{2}'.format(tests_ok, tests_fail, len(functions))

	import math
	
	L  = [1,2,3,4,5,6,7,8,9,10]
	M  = [4,5,6]
	E  = []
	D  = [1.1, 1.2, 3.1, 3.2, 3.3, 3.4, 3.5]
	W1 = ['The quick brown', 'fox jumps over', 'the lazy dogs']
	W2 = [['The', 'quick', 'brown'], ['fox', 'jumps', 'over'], ['the', 'lazy', 'dogs']]
	G  = ['blueberry', 'chimpanzee', 'abacus', 'banana', 'apple', 'cheese']
	R  = [6,10,5,2,8,9,4,1,3,7]
	S1 = [0,2,4,5,6,8,9]
	S2 = [1,3,5,7,8]
		
	# Query_Restriction.where

	@returns([2, 4, 6, 8, 10])
	def test_restriction_where():
		return Query(L).where(lambda n: n % 2 == 0).tolist()

	# Query_Projection.select

	@returns([2, 4, 6, 8, 10, 12, 14, 16, 18, 20])
	def test_projection_select():
		return Query(L).select(lambda n: n * 2).tolist()

	# Query_Projection.selectmany

	@returns(['The', 'quick', 'brown', 'fox', 'jumps', 'over', 'the', 'lazy', 'dogs'])
	def test_projection_selectmany_1():
		return Query(W1) \
			.selectmany(lambda s: s.split(' ')) \
			.tolist()

	@returns(['he', 'uick', 'rown', 'ox', 'umps', 'ver', 'he', 'azy', 'ogs'])
	def test_projection_selectmany_2():
		return Query(W1) \
			.selectmany(lambda s: s.split(' '), lambda s: s[1:]) \
			.tolist()

	@returns(['The', 'quick', 'brown', 'fox', 'jumps', 'over', 'the', 'lazy', 'dogs'])
	def test_projection_selectmany_3():
		return Query(W2) \
			.selectmany(lambda sx: sx) \
			.tolist()

	# Query_Partitioning.take

	@returns([1, 2, 3])
	def test_partitioning_take():
		return Query(L).take(3).tolist()

	# Query_Partitioning.skip

	@returns([8, 9, 10])
	def test_partitioning_skip():
		return Query(L).skip(7).tolist()

	# Query_Partitioning.takewhile

	@returns([1, 2, 3])
	def test_partitioning_takewhile():
		return Query(L).takewhile(lambda n: n < 4).tolist()

	# Query_Partitioning.skipwhile

	@returns([8, 9, 10])
	def test_partitioning_skipwhile():
		return Query(L).skipwhile(lambda n: n < 8).tolist()

	# TODO: Query_Ordering
	@returns([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
	def test_ordering_orderby():
		return Query(R).orderby(lambda n: n)

	# Query_Grouping.groupby

	@returns({'b':['blueberry', 'banana'], 'c':['chimpanzee', 'cheese'], 'a':['abacus', 'apple']})
	def test_grouping_groupby():
		return Query(G) \
			.groupby(lambda s: s[0]) \
			.select(lambda (key, items): (key, items.tolist())) \
			.todict()

	# Query_Sets.distinct
	
	@returns([2, 3, 5])
	def test_sets_distinct():
		return Query([2, 2, 3, 5, 5]) \
			.distinct() \
			.tolist()
	
	# Query_Sets.union
	
	@returns([0, 2, 4, 5, 6, 8, 9, 1, 3, 2])
	def test_sets_union():
		return Query(S1) \
			.union(Query(S2)) \
			.tolist()
	
	# Query_Sets.intersect
	
	@returns([5, 8])
	def test_sets_interect():
		return Query(S1) \
			.intersect(Query(S2)) \
			.tolist()
		
	# Query_Sets.difference
	
	@returns([0, 2, 4, 6, 9])
	def test_sets_difference():
		return Query(S1) \
			.intersect(Query(S2)) \
			.tolist()

	# Query_Conversion.todict

	@returns({1:2, 2:4, 3:6, 4:8})
	def test_conversion_todict_1():
		return Query(L) \
			.where(lambda n: n <= 4) \
			.select(lambda n: (n, 2*n)) \
			.todict()

	@returns({1:2, 2:4, 3:6, 4:8})
	def test_conversion_todict_2():
		return Query(L) \
			.where(lambda n: n <= 4) \
			.todict(lambda n: 2 * n)

	@returns({2:3, 4:6, 6:9, 8:12})
	def test_conversion_todict_3():
		return Query(L) \
			.where(lambda n: n <= 4) \
			.todict(lambda n: 2 * n, lambda n: 3 * n)

	# Query_Element.elementat

	@returns(1)
	def test_element_elementat_1():
		return Query(L).elementat(0)

	@returns(10)
	def test_element_elementat_2():
		return Query(L).elementat(9)

	# Query_Element.first

	@returns(1)
	def test_element_first_1a():
		return Query(L).first()

	@raises(ValueError)
	def test_element_first_1b():
		return Query(E).first()

	@returns(3.1)
	def test_element_first_2a():
		return Query(D).first(lambda n: 3 <= n <= 4)

	@raises(ValueError)
	def test_element_first_2b():
		return Query(E).first(lambda n: 3 <= n <= 4)

	# Query_Element.last

	@returns(10)
	def test_element_last_1a():
		return Query(L).last()

	@raises(ValueError)
	def test_element_last_1b():
		return Query(E).last()

	@returns(3.5)
	def test_element_last_2a():
		return Query(D).last(lambda n: 3 <= n <= 4)

	@raises(ValueError)
	def test_element_last_2b():
		return Query(E).last(lambda n: 3 <= n <= 4)

	# Query_Element.firstordefault

	@returns(1)
	def test_element_firstordefault_1():
		return Query(L).firstordefault()

	@returns(42)
	def test_element_firstordefault_2():
		return Query(E).firstordefault(default=42)

	# Query_Element.single

	@returns(4)
	def test_element_single_1a():
		return Query(L).where(lambda n: n == 4).single()

	@raises(ValueError)
	def test_element_single_1b():
		return Query(L).where(lambda n: n < 4).single()

	@raises(ValueError)
	def test_element_single_1c():
		return Query(L).where(lambda n: n >= 4).single()

	@returns(4)
	def test_element_single_2a():
		return Query(L).single(lambda n: n == 4)

	@raises(ValueError)
	def test_element_single_2b():
		return Query(L).single(lambda n: n < 4)

	@raises(ValueError)
	def test_element_single_2c():
		return Query(L).single(lambda n: n >= 4)

	# Query_Element.singleordefault

	@returns(4)
	def test_element_singleordefault_1a():
		return Query(L).where(lambda n: n == 4).singleordefault(default=42)

	@returns(42)
	def test_element_singleordefault_1b():
		return Query(L).where(lambda n: n > 10).singleordefault(default=42)

	@raises(ValueError)
	def test_element_singleordefault_1c():
		return Query(L).where(lambda n: n < 4).singleordefault(default=42)

	@raises(ValueError)
	def test_element_singleordefault_1d():
		return Query(L).where(lambda n: n >= 4).singleordefault(default=42)

	@returns(4)
	def test_element_singleordefault_2a():
		return Query(L).singleordefault(lambda n: n == 4, default=42)

	@returns(42)
	def test_element_singleordefault_2b():
		return Query(L).singleordefault(lambda n: n > 10, default=42)

	@raises(ValueError)
	def test_element_singleordefault_2c():
		return Query(L).singleordefault(lambda n: n < 4, default=42)

	@raises(ValueError)
	def test_element_singleordefault_2d():
		return Query(L).singleordefault(lambda n: n >= 4, default=42)

	# TODO: Query_Generation

	# Query_Quantifiers.any
	
	@returns(True)
	def test_quantifiers_any_1a():
		return Query([False, False, True]).any()

	@returns(False)
	def test_quantifiers_any_1b():
		return Query([False, False, True]).any()
	
	@returns(True)
	def test_quantifiers_any_2a():
		return Query(L).any(lambda n: n <= 1)
	
	@returns(False)
	def test_quantifiers_any_2b():
		return Query(L).any(lambda n: n < 1)

	# Query_Quantifiers.all
	
	@returns(True)
	def test_quantifiers_all_1a():
		return Query([True, True, True]).all()
	
	@returns(False)
	def test_quantifiers_all_1b():
		return Query([True, True, False]).all()
		
	@returns(True)
	def test_quantifiers_all_2a():
		return Query(L).all(lambda n: n > 0)
	
	@returns(False)
	def test_quantifiers_all_2b():
		return Query(L).all(lambda n: n > 1)
			
	# Query_Aggregates.aggregate

	@returns(sum(range(1,11)))
	def test_aggregates_aggregate_1():
		return Query(L).aggregate(lambda a,b: a + b, initial=0)

	@returns(math.factorial(10))
	def test_aggregates_aggregate_2():
		return Query(L).aggregate(lambda a,b: a * b, initial=1)

	@raises(TypeError)
	def test_aggregates_aggregate_3():
		return Query(L).aggregate(lambda a,b: a + b)

	# TODO: Query_Aggregates.sum
	@returns(sum(range(1, 11)))
	def test_aggregates_sum_1a():
		return Query(L).sum()
	
	@raises(ValueError)
	def test_aggregates_sum_1b():
		return Query(E).sum()
		
	@returns(sum(range(2, 22, 2)))
	def test_aggregates_sum_2a():
		return Query(L).sum(lambda n: 2 * n)
	
	@raises(ValueError)
	def test_aggregates_sum_2b():
		return Query(E).sum(lambda n: 2 * n)

	# TODO: Query_Aggregates.average

	# Query_Aggregates.min

	@returns(1)
	def test_aggregates_min_1a():
		return Query(L).min()

	@raises(ValueError)
	def test_aggregates_min_1b():
		return Query(E).min()

	@returns(5)
	def test_aggregates_min_2a():
		return Query(L).min(lambda n: n >= 5)

	@raises(ValueError)
	def test_aggregates_min_2b():
		return Query(E).min(lambda n: n >= 5)

	# Query_Aggregates.max

	@returns(10)
	def test_aggregates_max_1a():
		return Query(L).max()

	@raises(ValueError)
	def test_aggregates_max_1b():
		return Query(E).max()

	@returns(5)
	def test_aggregates_max_2a():
		return Query(L).max(lambda n: n <= 5)

	@raises(ValueError)
	def test_aggregates_max_2b():
		return Query(E).max(lambda n: n <= 5)

	# Query_Aggregates.count

	@returns(5)
	def test_aggregates_count_1a():
		return Query(L).where(lambda n: n <= 5).count()

	@returns(0)
	def test_aggregates_count_1b():
		return Query(L).where(lambda n: n > 10).count()

	@returns(5)
	def test_aggregates_count_2a():
		return Query(L).count(lambda n: n <= 5)

	@returns(0)
	def test_aggregates_count_2b():
		return Query(L).count(lambda n: n > 10)

	run_tests()
