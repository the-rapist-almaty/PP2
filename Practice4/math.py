import math
#1
degree = int(input('Degrees '))
print(f'Radians {math.radians(degree)}')

#2
height = int(input('Height '))
base1 = int(input('Base 1 '))
base2 = int(input('Base 2 '))
print(f'Area of trapeziod {(base1+base2) * height/2}')

#3
number_of_sides = int(input('Number of sides '))
side_length = int(input('Side length '))
print(f'Area of polygon {(number_of_sides * math.pow(side_length, 2)) / (4 * math.tan(math.pi/number_of_sides))}')

#4
base = int(input('Base '))
height = int(input('Height '))
print(f'Area of parallelogram {base*height}')