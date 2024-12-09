from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debag >>> ')

ic.disable()  # Отключить вывод
ic.enable()  # Включить вывод


a = 10
b = 20

ic(a, b, a+b)