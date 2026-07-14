class Counter:
    def __init__(self):
        self.n = 0
    def inc(self):
        self.n += 0  # bug
    def value(self):
        return self.n
