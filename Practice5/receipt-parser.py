import re
import json

with open('raw.txt', 'r') as file:
    content = file.read()

prices_res =[]
prices = re.findall("Стоимость\n[0-9]* *[0-9]+,[00-99]", content)
for i in prices:
    prices_res.append(i[10:])

#print('All prices for receipt:', prices_res)

names_res = []
names = re.findall("\.\n.+", content)
for i in names:
    names_res.append(i[2:])

#print('All product names from receipt:', names_res)

total = re.findall('ИТОГО:\n.*', content)
#print('Total:', total[0][7:])

time = re.findall('Время: .+', content)
#print('Время: ', time[0][7:])

payment_method_raw = re.findall('.+\n.+\nИТОГО:', content)
payment_method = re.findall('.+\n[0-9]', payment_method_raw[0])
#print('Payment method:', payment_method[0][:len(payment_method)-4])

name_price = {}
for i in range(len(names_res)):
    name_price[names_res[i]] = prices_res[i]

receipt_info ={ "Date and time" : time[0][7:],
                "Payment method" :payment_method[0][:len(payment_method)-4],
                "Product": name_price
                }
x = json.dumps(receipt_info, ensure_ascii=False, indent=4)
print(x)