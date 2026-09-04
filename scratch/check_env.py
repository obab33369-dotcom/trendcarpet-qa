import os
from concurrent.futures import ProcessPoolExecutor

def get_env():
    return os.environ.get('TEST_VAR')

if __name__ == '__main__':
    os.environ['TEST_VAR'] = 'HELLO'
    executor = ProcessPoolExecutor(1)
    future = executor.submit(get_env)
    print("Env inherited:", future.result())
