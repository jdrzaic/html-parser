PUBLIC_KEY = "PUBLIC"
SYSTEM_KEY = "SYSTEM"


class Node(object):
    pass


class DocumentType(object):
    pass


class Document(Node):
    def __init__(self, url):
        self.url = url
