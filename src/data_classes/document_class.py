"""
Example of a document class that can be used to represent a document in a system.

    Document{
        id = "doc-001",
        name = "engine requirements",
        document_type = "requirement",
        version = "1.0",
        status = "created"
    }

"""


class Document:
    def __init__(self, id_, name, document_type, version, status):
        self.id = id_
        self.name = name
        self.document_type = document_type
        self.version = version
        self.status = status
