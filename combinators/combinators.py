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

sqrange = lambda n: takewhile(lambda a: a * a <= n, count(1))
limit   = lambda n, L: [v2 for (v1, v2) in izip(xrange(n), L)]
factors = lambda n: (v for v in sqrange(n) if not n % v)
ffac    = lambda n: limit(2, factors(n))[-1]
pfac1   = S(lambda f, n:
            (lambda i: [n] if i == 1 else f(f, i) + f(f, n / i))(i=ffac(n)))
pfac2   = Y(lambda f: lambda n:
            (lambda i: [n] if i == 1 else f(i) + f(n / i))(i=ffac(n)))

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
    
    assert limit(2, [1, 2, 3]) == [1, 2]
    
    assert list(factors(10)) == [1, 2]
    
    assert ffac(10) == 2
    assert ffac(5) == 1
    
    assert pfac1(10) == [2, 5]
    
    assert pfac2(10) == [2, 5]
    assert pfac2(20) == [2, 2, 5]
    
    assert fact1(4) == 24
    assert fact2(4) == 24
    
    assert fib1(4) == 5
    