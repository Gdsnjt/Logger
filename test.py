import multiprocessing

class Singleton:
    _instance = None
    value = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

def worker():
    s = Singleton()
    print(f"Worker: {s.value}, id={id(s)}")  # None と表示される

if __name__ == '__main__':
    s = Singleton()
    s.value = "main"
    print(f"Main: {s.value}, id={id(s)}")
    
    p = multiprocessing.Process(target=worker)
    p.start()
    p.join()
    # Output:
    # Main: main, id=123456
    # Worker: None, id=789012  # 違うインスタンス！