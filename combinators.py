#!/usr/bin/python

from itertools import count, takewhile, izip

S = (lambda f: 
        (lambda x: f(f, x)))
Y = (lambda F: 
        (lambda g: g(g))
        (lambda f: 
            F(lambda x: f(f)(x))))

#S = lambda f: (lambda *a, **k: f(f, *a, **k))
#Y = lambda F: (lambda g: g(g))(lambda f: F(lambda *a, **k: f(f)(*a, **k)))

def last(seq):
    for item in seq:
        pass
    return item

sqrange = lambda n: takewhile(lambda a: a * a <= n, count(1))
factors = lambda n: (v for v in sqrange(n) if not n % v)
take    = lambda n, seq: (lambda i: (i.next() for _ in xrange(n)))(iter(seq))
ffac    = lambda n: last(take(2, factors(n)))

pfac1   = S(lambda f, n:
            (lambda i: [n] if i == 1 else f(f, i) + f(f, n / i))(ffac(n)))
pfac2   = Y(lambda f: lambda n:
            (lambda i: [n] if i == 1 else f(i) + f(n / i))(ffac(n)))
pfac3   = Y(lambda f: lambda n:
            (lambda i=ffac(n): [n] if i == 1 else f(i) + f(n / i))())
            
fact1   = S(lambda f, n: 
            1 if n == 1 else n * f(f, n - 1))
fact2   = Y(lambda f: lambda n: 
            1 if n == 1 else n * f(n - 1))
            
fib1    = S(lambda f, n:
            1 if n < 2 else f(f, n - 1) + f(f, n - 2))
fib2    = Y(lambda f: lambda n:
            1 if n < 2 else f(n - 1) + f(n - 2))

if __name__ == '__main__':
    assert list(sqrange(10)) == [1, 2, 3]
    
    assert list(take(2, [])) == []
    assert list(take(2, [1])) == [1]
    assert list(take(2, [1, 2])) == [1, 2]
    assert list(take(2, [1, 2, 3])) == [1, 2]
    
    assert list(factors(10)) == [1, 2]
    
    assert ffac(10) == 2
    assert ffac(5) == 1
    
    assert pfac1(10) == [2, 5]
    
    assert pfac2(10) == [2, 5]
    assert pfac2(20) == [2, 2, 5]
    
    assert pfac3(160) == [2, 2, 2, 2, 2, 5]
    assert pfac3(123456789012345) == [3, 5, 283, 3851, 7552031]
    assert pfac3(123456789012) == [2, 2, 3, 10288065751]
    
    assert fact1(4) == 24
    assert fact2(4) == 24
    
    assert fib1(4) == 5
    assert fib2(4) == 5
    
    