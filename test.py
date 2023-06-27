import random
import string

def generate_dummy_data(num_records):
    data = []
    for i in range(num_records):
        record = {
            'id': i + 1,
            'name': generate_random_string(10),
            'email': generate_random_email(),
            'age': random.randint(18, 65)
        }
        data.append(record)
    return data

def generate_random_string(length):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length))

def generate_random_email():
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'example.com']
    name = generate_random_string(5)
    domain = random.choice(domains)
    return f"{name}@{domain}"

# Generating 1000 dummy data records
dummy_data = generate_dummy_data(1000)

# Printing the generated data
for record in dummy_data:
    print(record)


