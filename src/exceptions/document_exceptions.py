class DocumentNotFoundError(Exception):
    """Raised when a document is not found in the database."""

    def __init__(self, document_id):
        self.document_id = document_id
        self.message = f"Document with ID '{document_id}' not found."
        super().__init__(self.message)


class InvalidDocumentError(Exception):
    """Raised when a document is invalid or does not meet the required criteria."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
