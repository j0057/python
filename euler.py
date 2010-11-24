#!/usr/bin/env python

from jtest import BaseTest, returns, raises, color
from pyquery import Query
from itertools import count
import sys

class Tests(BaseTest):
    pass
class Results(BaseTest):
    pass
def test(result, *args):
    def test_dec(f):
        def test_method(self):
            return f(*args)
        test_method.__name__ = f.__name__
        setattr(Tests, f.__name__, returns(result)(test_method))
        return f
    return test_dec
    
def result_of(*args):
    def result_of_dec(f):
        def test_method(self):
            return f(*args)
        test_method.__name__ = f.__name__
        test_method.is_test = True
        setattr(Results, f.__name__, test_method)
        return f
    return result_of_dec


###############################################################################    
    
def fibonacci():
	m, n = 0, 1
	while True:
		m, n = n, m + n
		yield m

def primes():
    p = [2, 3]
    n = 5
    s = 2
    yield 2
    yield 3
    while True:
        b = True
        for i in p:
            b = (n % i)
            if not b:
                break
            if i * i >= n:
                break
        if b:
            p.append(n)
            yield n
        n += s
        s ^= 6
        
def factors(n):
    return Query(count(1)) \
        .take_while(lambda i: i * i <= n) \
        .where(lambda i: n % i == 0)

def prime_factors(n):
    first = Query(factors(n)).take(2).last()
    return [n] if first == 1 else (prime_factors(first) + prime_factors(n / first))

        
###############################################################################    

@result_of(1000)
@test(23, 10)
def euler_001(n):
    '''n -> all the natural numbers below n that are multiples of 3 or 5'''
    return Query(xrange(1, n)) \
        .where(lambda i: i % 3 == 0 or i%5==0) \
        .sum()

@result_of(4000000)
@test(44, 90)
def euler_002(n):
    'n -> sum of all the even-valued terms in the Fibonacci sequence which do not exceed n'
    return Query(fibonacci()) \
        .skip(1) \
        .take_while(lambda i: i <= n) \
        .where(lambda i: i & 1 == 0) \
        .sum()

@result_of(600851475143)
@test(29, 13195)
def euler_003(n):
    'n -> largest prime factor of n'
    return Query(prime_factors(n)).last()

@result_of(3)
@test(9009, 2)
def euler_004(n):
    'n -> largest palindrome made from the product of two n-digit numbers'
    digits = lambda n: xrange(10**(n-1),10**n)
    return Query(digits(n)) \
        .select_many(lambda i: digits(n), lambda a, b: a * b) \
        .where(lambda i: str(i) == str(i)[::-1]) \
        .max()

@result_of(20)
@test(2520, 10)
def euler_005(n):
    'n -> smallest number divisible by each of the numbers 1 to n'
    factors = {}
    for i in xrange(2,n+1):
        for k,g in Query(prime_factors(i)) \
                .group_by() \
                .to_dict(lambda (k,g): k, lambda (k,g): g.count()) \
                .items():
            if k not in factors or g > factors[k]:
                factors[k] = g
    return Query(factors.items()) \
        .select(lambda (k, g): k ** g) \
        .aggregate(lambda a, b: a * b, 1)

@result_of(100)
@test(2640, 10)
def euler_006(n):
    'n ->  difference between the sum of the squares and the square of the sums of all natural numbers up to n'
    return (Query(xrange(1,n+1)).sum() ** 2) - Query(xrange(1,n+1)).select(lambda i: i ** 2).sum()
        
@result_of(10000)
@test(13, 5)
def euler_007(n):
    "n -> n'th prime"
    return Query(primes()).element_at(n)

@result_of(5)
@test(81, 2)
def euler_008(n):
    'n -> largest product of n consecutive digits in the 1000-digit number'
    s = '7316717653133062491922511967442657474235534919493496983520312774506326239578318016984801869478851843858615607891129494954595017379583319528532088055111254069874715852386305071569329096329522744304355766896648950445244523161731856403098711121722383113622298934233803081353362766142828064444866452387493035890729629049156044077239071381051585930796086670172427121883998797908792274921901699720888093776657273330010533678812202354218097512545405947522435258490771167055601360483958644670632441572215539753697817977846174064955149290862569321978468622482839722413756570560574902614079729686524145351004748216637048440319989000889524345065854122758866688116427171479924442928230863465674813919123162824586178664583591245665294765456828489128831426076900422421902267105562632111110937054421750694165896040807198403850962455444362981230987879927244284909188845801561660979191338754992005240636899125607176060588611646710940507754100225698315520005593572972571636269561882670428252483600823257530420752963450'
    return Query(xrange(len(s)-n+1)) \
        .select(lambda i: s[i:i+n]) \
        .select_many(lambda s: s.split(), lambda s,i: i) \
        .select(lambda s: Query(s).select(int).aggregate(lambda a, b: a * b, 1)) \
        .max()

@result_of(1000)
def euler_009(n):
    'n -> product the only Pythagorean triplet, {a, b, c}, for which a + b + c == n'
    for a in xrange(1, n):
        for b in xrange(a, n):
            if a + b >= n: 
                break
            c = n - a - b
            if a ** 2 + b ** 2 == c ** 2:
                return a * b * c
                    
@result_of(2000000)
@test(17, 10)
def euler_010(n):
    'n -> sum of all the primes below n'
    return Query(primes()) \
        .take_while(lambda i: i < n) \
        .sum()

@result_of(1000)
@test(12, 3)
def euler_025(n):
    'n -> first term in the Fibonacci sequence to contain n digits'
    return Query(fibonacci()) \
        .take_while(lambda i: len(str(i)) < n) \
        .count() + 1

###############################################################################    

if __name__ == '__main__':
    color.ENABLED = sys.stdout.isatty()
    BaseTest.run_all_tests(base_class=BaseTest, g=globals())
