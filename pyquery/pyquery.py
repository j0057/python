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
	
	def selectmany(self, func):
		pass

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
	pass

class Query_Sets(Query_Base):
	pass

class Query_Conversion(Query_Base):
	def tolist(self):
		return list(self)
	
	def todict(self, func=None):
		if func:
			return dict((i, func(i)) for i in self)
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
	def aggregate(self, func, initial=0):
		result = initial
		for item in self:
			result = func(result, item)
		return result
	
	def sum(self):
		return self.aggregate(lambda a, b: a + b)
		
	def average(self):
		return float(self.sum()) / self.count()
	
	def min(self):
		lowest = self.first()
		for item in self.skip(1):
			if item < lowest:
				lowest = item
		return lowest
	
	def max(self):
		highest = self.first()
		for item in self.skip(1):
			if item > highest:
				highest = item
		return highest
	
	def count(self):
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
	def assert_throws(stmt, exc_class, msg=None):
		try:
			stmt()
			raise AssertionError('No exception of type {0} raised; {1}'.format(exc_class.__name__, msg))
		except Exception as e:
			assert type(e) == exc_class, msg

	L = [1,2,3,4,5,6,7,8,9,10]
	E = []
	D = [1.1, 1.2, 3.1, 3.2, 3.3, 3.4, 3.5]

	import unittest
	class QueryTestCase(unittest.TestCase):
		def setUp(self):
			self.L = [1,2,3,4,5,6,7,8,9,10]
			self.E = []
			self.D = [1.1, 1.2, 3.1, 3.2, 3.3, 3.4, 3.5]
	class TestRestriction(QueryTestCase):
		def test_where(self):
			assert Query(self.L) \
				.where(lambda n: n % 2 == 0) \
				.tolist() == [2, 4, 6, 8, 10]
	class TestProjection(QueryTestCase):
		def test_select(self):
			assert Query(self.L) \
				.select(lambda n: 2 * n) \
				.tolist() == [2,4,6,8,10,12,14,16,18,20]
	class TestPartitioning(QueryTestCase):
		def test_take(self):
			assert Query(self.L) \
				.take(3) \
				.tolist() == [1,2,3]
		def test_skip(self):
			assert Query(self.L) \
				.skip(7) \
				.tolist() == [8,9,10]
		def test_skip_take(self):
			assert Query(self.L) \
				.skip(5) \
				.take(3) \
				.tolist() == [6,7,8]
		def test_takewhile(self):
			assert Query(self.L) \
				.takewhile(lambda n: n < 4) \
				.tolist() == [1,2,3]
		def test_skipwhile(self):
			assert Query(self.L) \
				.skipwhile(lambda n: n < 8) \
				.tolist() == [8,9,10]



	tests = unittest.TestSuite([ unittest.makeSuite(c, 'test_') for c in [
		TestRestriction,
		TestProjection,
		TestPartitioning]])
	unittest.TextTestRunner().run(tests)
	

	# ordering
	
	# grouping
	
	# sets
	
	# conversion
	assert Query(L) \
		.where(lambda n: n <= 4) \
		.select(lambda n: (n, 2*n)) \
		.todict() == {1:2, 2:4, 3:6, 4:8}, '.todict #1'
	
	assert Query(L) \
		.where(lambda n: n <= 4) \
		.todict(lambda n: 2 * n) == {1:2, 2:4, 3:6, 4:8}, '.todict #2'
	
	# element
	assert Query(L).elementat(0) == 1, '.elementat #1'
	assert Query(L).elementat(9) == 10, '.elementat #2'
	
	assert Query(L).first() == 1, '.first #1'	
	assert_throws(lambda: Query(E).first(), ValueError, '.first #2')
	assert Query(L).first(lambda n: n == 4) == 4, '.first #3'
	assert_throws(lambda: Query(E).first(lambda n: n == 4), ValueError, '.first #4')
	
	assert Query(L).last() == 10, '.last #1'
	assert_throws(lambda: Query(E).last(), ValueError, '.last #2')
	assert Query(D).last(lambda n: 3 <= n <= 4) == 3.5, '.last #3'
	assert_throws(lambda: Query(E).last(lambda n: 3 <= n <= 4), ValueError, '.last #4')

	assert Query(L).firstordefault() == 1, '.firstordefault #1'
	#assert_throws(lambda: Query(E).firstordefault(), ValueError, '.firstordefault #2')
	#assert Query(D).firstordefault(lambda n: 3 <= n <= 4) == 3.1, '.firstordefault #3'
	#assert_throws(lambda: Query(E).firstordefault(lambda n: 3 <= n <= 4), ValueError, '.firstordefault #4')
	
	# generation
	
	# quantifiers
	
	# aggregates
	assert Query(L) \
		.aggregate(lambda a,b: a+b) == sum(L), '.aggregate #1'
	assert Query(L) \
		.aggregate(lambda a,b: a*b, 1) == reduce(lambda a,b: a*b, L, 1), '.aggregate #2'
	
	assert Query(L).min() == 1, '.min #1'
	assert_throws(lambda: Query(E).min(), ValueError, '.min #2')
	
	assert Query(L).max() == 10, '.max #2'
	assert_throws(lambda: Query(E).max(), ValueError, '.max #2')
	
	assert Query(L).count() == 10, '.count #1'
	assert Query(E).count() == 0, '.count #2'
	
	assert Query(L).sum() == 55, '.sum #1'
	assert Query(E).sum() == 0, '.sum #2'
	
	assert Query(L).average() == 5.5, '.average #1'