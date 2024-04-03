from dataclasses import dataclass

@dataclass
class Transaction:
    data: str


tr = Transaction('hello 2')
tr1 = Transaction('hello 2')

l = [tr1]

print(tr in l)