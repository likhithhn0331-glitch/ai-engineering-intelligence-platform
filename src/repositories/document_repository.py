from src.data_classes.document_class import Document
from src.database import initialize_database
from src.db.connection import DatabaseConfigurationError, database_connection, get_database_url


class DocumentRepository:
    def __init__(self):
        self.documents = {}
        self.use_postgres = False
        if get_database_url():
            try:
                initialize_database()
                self.use_postgres = True
            except Exception:
                self.use_postgres = False

    @staticmethod
    def _row_to_document(row):
        if not row:
            return None
        return Document(
            id_=row[0],
            name=row[1],
            document_type=row[2],
            version=row[3],
            status=row[4],
        )

    def create_document(self, document: Document):
        if self.use_postgres:
            try:
                with database_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO documents (id, name, document_type, version, status, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                            """,
                            (document.id, document.name, document.document_type, document.version, document.status),
                        )
                        connection.commit()
                return document
            except (DatabaseConfigurationError, RuntimeError):
                self.use_postgres = False

        self.documents[document.id] = document
        return document

    def get_document(self, document_id):
        if self.use_postgres:
            try:
                with database_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT id, name, document_type, version, status FROM documents WHERE id = %s",
                            (document_id,),
                        )
                        row = cursor.fetchone()
                        return self._row_to_document(row)
            except (DatabaseConfigurationError, RuntimeError):
                self.use_postgres = False

        return self.documents.get(document_id)

    def delete_document(self, document_id):
        if self.use_postgres:
            try:
                with database_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM documents WHERE id = %s RETURNING id", (document_id,))
                        deleted = cursor.fetchone() is not None
                        connection.commit()
                        return deleted
            except (DatabaseConfigurationError, RuntimeError):
                self.use_postgres = False

        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False

    def list_documents(self):
        if self.use_postgres:
            try:
                with database_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT id, name, document_type, version, status FROM documents ORDER BY created_at ASC, id ASC"
                        )
                        return [self._row_to_document(row) for row in cursor.fetchall()]
            except (DatabaseConfigurationError, RuntimeError):
                self.use_postgres = False

        return list(self.documents.values())

    def update_document(self, document_id, updated_data):
        if self.use_postgres:
            try:
                allowed_fields = {"name", "document_type", "version", "status"}
                if not updated_data:
                    return self.get_document(document_id)

                updates = []
                values = []
                for key, value in updated_data.items():
                    if key in allowed_fields:
                        updates.append(f"{key} = %s")
                        values.append(value)

                if not updates:
                    return self.get_document(document_id)

                values.append(document_id)
                with database_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            f"UPDATE documents SET {', '.join(updates)}, updated_at = NOW() WHERE id = %s RETURNING id, name, document_type, version, status",
                            tuple(values),
                        )
                        row = cursor.fetchone()
                        connection.commit()
                        return self._row_to_document(row)
            except (DatabaseConfigurationError, RuntimeError):
                self.use_postgres = False

        document = self.documents.get(document_id)
        if not document:
            return None
        for key, value in updated_data.items():
            if hasattr(document, key):
                setattr(document, key, value)
        return document

    def update(self, document_id, updated_data):
        return self.update_document(document_id, updated_data)
