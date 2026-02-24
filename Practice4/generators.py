#1
print('===FIRST===')

def first(fst):
    for i in range(1, fst+1):
        yield i*i
n = int(input('Input N: '))
gen = first(n)
for i in gen:
    print(i)   

#2 
print('===SECOND===')
def second(scnd):
    for i in range(1, scnd+1):
        if i % 2 == 0: yield i
n = int(input('Input N: '))
gen = second(n)
res = ''
for i in gen:
    res += str(i) + ','   
print(res)

#3
print('===THIRD===')
def third(n):
    for i in range(0, n + 1):
        if i % 3 == 0 and i % 4 == 0: yield i
n = int(input("Enter N: "))
for number in third(n):
    print(number)

#4
print('===FOURTH===')
def squares(a,b):
    for i in range(a,b): yield i*i
res = squares(2,7)
for i in res:
    print(i)

#5
print('===FIFTH====')
def fifth(ft):
    while ft:
        yield ft
        ft-=1 
    yield 0
res = fifth(10)
for i in res:
    print(i)