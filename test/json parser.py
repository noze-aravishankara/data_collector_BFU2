import json

with open('output.json', 'r') as f:
    _ = json.load(f)

# STEP 1: Get just the data
data = _['t']

# STEP 2: Parse data and get headers only
# headers = []
# for d in data:
#     headers.append(list(d.keys())[0])

headers = [list(d.keys())[0] for d in data]

# STEP 3: Parse and only get values
value = [list(d.values())[0] for d in data]

print(value)