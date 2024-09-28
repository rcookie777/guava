class NewsItem:
    def __init__(self, title, url):
        self.title = title
        self.url = url

    def to_dict(self):
        return {
            'title': self.title,
            'url': self.url
        }
class DataItem:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def to_dict(self):
        return {
            'name': self.name,
            'value': self.value
        }
