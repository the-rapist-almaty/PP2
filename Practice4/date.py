import datetime

print(f'Number 1 {datetime.date.today() - datetime.timedelta(days=5)}')
print(f'Number 2 {datetime.date.today() - datetime.timedelta(days=1)} , {datetime.date.today()} , {datetime.date.today() + datetime.timedelta(days=1)}')
print(f'Number 3 {datetime.datetime.now().replace(microsecond=0)}')
print(f'Number 5')
x1 = input('Enter date 1 (Fromat it like YYYY-MM-DD HH:MM:SS) ')
x2 = input('Enter date 2 (Fromat it like YYYY-MM-DD HH:MM:SS) ')
x1_date = datetime.datetime.strptime(x1, '%Y-%m-%d %H:%M:%S')
x2_date = datetime.datetime.strptime(x2, '%Y-%m-%d %H:%M:%S')
print(x1_date-x2_date, ' seconds')