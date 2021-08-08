
# TODO Add db integration

class Feed:
    def __init__(self, url, name, items=[]):
        self.name = name
        self.url = url

        self.items = items

    def fetch(self):
        pass


