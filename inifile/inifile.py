#!/usr/bin/python

class Map(object):
    def __init__(self):
		# bypass __setattr__
		self.__dict__['_Map__map'] = []

    def __len__(self):
        return len(self.__map)

    def __getattr__(self, key):
        for k, v in self.__map:
            if k == key:
                return v
        else:
            raise KeyError(key)

    def __setattr__(self, key, value):
        for (i, (k, v)) in enumerate(self.__map):
            if k == key:
                self.__dict__['_Map__map'][i] = (key, value)
                break
        else:
            self.__dict__['_Map__map'] += [(key, value)]

    def __delattr__(self, key):
        for (i, (k, v)) in enumerate(self.__map):
            if k == key:
                del self.__map[i]
                break
        else:
            raise KeyError(key)

    def __getitem__(self, item):
        if isinstance(item, str):
            return getattr(self, item)
        else:
            return self.__map[item]

    def __setitem__(self, item, value):
        if isinstance(item, str):
            setattr(self, item, value)
        else:
            self.__map[item] = value

    def __delitem__(self, item):
        if isinstance(item, str):
            delattr(self, item)
        else:
            self.__map[item]

    def put(self, key, value): self[key] = value
    def get(self, key): return self[key]
    def remove(self, key): del self[key]

    def keys(self):   return [ k for (k, v) in self.__map ]
    def values(self): return [ v for (k, v) in self.__map ]
    def items(self):  return [ t for t      in self.__map ]

class INIFile(Map):
    def __init__(self, filename=None, autosection=False):
        Map.__init__(self)
        if filename:
            self.read(filename)
        self.__dict__['_INIFile__autosection'] = autosection

    def __str__(self):
        return '\n'.join('[%s]\n%s' % (name, str(section))
                         for (name, section) in self.items())

    def __getattr__(self, key):
        try:
            return Map.__getattr__(self, key)
        except KeyError:
            if self.__autosection:
                self.add(key)
            return Map.__getattr__(self, key)

    def __setattr__(self, key, value):
        if not isinstance(value, INISection):
            raise TypeError(type(value).__name__)
        return Map.__setattr__(self, key, value)

    def __setitem__(self, item, value):
        if not isinstance(value, INISection):
            raise TypeError(type(value).__name__)
        return Map.__setitem__(self, item, value)

    def add(self, section):
        self[section] = INISection()

    def read(self, filename):
        f = open(filename, 'r')
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('[') and line.endswith(']'):
                section = line[1:-1]
                self.add(section)
            else:
                k, v = line.split('=', 1)
                self[section][k] = v
        f.close()

    def write(self, filename):
        f = open(filename, 'w')
        f.write(str(self))
        f.close()

class INISection(Map):
    def __str__(self):
        return '\n'.join('%s=%s' % (k, v)
                         for (k, v) in self.items()) + '\n'

def read(filename):
	return INIFile(filename)

if __name__ == '__main__':
	def test_map():
		m = Map()
		try:
			print m.foo
			assert False
		except Exception as e:
			assert isinstance(e, KeyError), e.__class__.__name__
			assert e.args == ('foo',), repr(e.args)
		try:
			del m.foo
			assert False
		except Exception as e:
			assert isinstance(e, KeyError), e.__class__.__name__
			assert e.args == ('foo',), repr(e.args)
		assert m.keys() == [], m.keys()
		m.foo = 42
		assert m.keys() == ['foo'], m.keys()
		assert m.values() == [42], m.values()
		assert m.items() == [('foo',42)], m.items()
		assert m.foo == 42, m.foo
		assert m[0] == ('foo', 42), m[0]
		m.foo = 43
		del m.foo
		try:
			print m.foo
			assert False
		except Exception as e:
			assert isinstance(e, KeyError), e.__class__.__name__
			assert e.args == ('foo',), repr(e.args)
