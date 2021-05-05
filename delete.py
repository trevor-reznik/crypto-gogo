i = """Bitcoin (BTC)

0.25%

0.0005 BTC

8

US Dollar (USD)

2%

1 USD

4

Euro (EUR)

1.5%

1 EUR

4"""

i = i.split("\n")
ret =[]
x = 0
while x < len(i)-5:
    curr = "| " + i[x]
    curr += " | " + i[x+2]
    curr += " | " + i[x+4]
    curr += " | " + i[x+6] + " |"
    ret.append(curr)
    x += 8

for _ in ret:
    print(_)