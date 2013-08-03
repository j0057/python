#!/usr/bin/env python2.7
import imp, time, sh
sh = imp.load_source('sh', 'sh/sh.py')
print sh
prev = []
while 1:
    lines = sh.run('netstat -vetupan').split('\n')[2:]
    for line in lines:
        if hash(line) not in prev:
            print line
    prev = [ hash(line) for line in lines ]
    time.sleep(0.5)
    


