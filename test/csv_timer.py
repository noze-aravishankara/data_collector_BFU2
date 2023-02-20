import threading
import csv
import timeit
import logging

logging.basicConfig(level=logging.INFO)

my_array = [2000000, 17493, 214552, 25677, 604, 43539, 74202, 11845, 290237, 5663, 76998, 2000000, 375204, 3547, 671980,
            5528, 96133, 23115, 87690, 36026, 123858, 171958, 68746, 11243, 60580, 6957, 22163, 5251, 10598, 78807,
            565524, 353885, 179674, 24.68, 21.1, 997.7, 114209.23, -1, 'baseline']


def update_array(data):
    with open('test.csv', 'a', newline='') as f:
        csv_writer = csv.writer(f, delimiter=',')
        csv_writer.writerow(data)
        logging.info('UPDATED ARRAY')
        f.close()
    return None

def threaded_call():
    _ = threading.Thread(target=update_array, args=(my_array,))
    _.start()
    _.join()
    logging.info('STARTED NEW THREAD')
    return None

def main():
    print(timeit.repeat(stmt=threaded_call, repeat=5, number=10))


if __name__ == '__main__':
    main()

