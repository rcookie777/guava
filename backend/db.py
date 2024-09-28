from pymongo import MongoClient
from pymongo.collection import Collection
from typing import List, Dict


class MongoDBClient:
    def __init__(self, uri: str, cert_file: str, db_name: str, collection_name: str):
        self.uri = uri
        self.cert_file = cert_file
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection: Collection = None

    def login(self):
        """Connect to MongoDB using provided URI and certificate."""
        try:
            self.client = MongoClient(
                self.uri,
                tls=True,
                tlsCertificateKeyFile=self.cert_file
            )
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            print(f"Successfully connected to {self.db_name}.{self.collection_name}")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

    def add_data(self, vector: Dict[str, float]) -> str:
        """Insert a new 3D vector into the collection."""
        try:
            insert_result = self.collection.insert_one(vector)
            print(f"Inserted document with _id: {insert_result.inserted_id}")
            return insert_result.inserted_id
        except Exception as e:
            print(f"Failed to insert document: {e}")

    def read_data(self, query: Dict = None) -> List[Dict]:
        """Read documents from the collection based on the query."""
        try:
            if query is None:
                query = {}
            documents = self.collection.find(query)
            result = list(documents)
            for doc in result:
                print(doc)
            return result
        except Exception as e:
            print(f"Failed to read data: {e}")
            return []

    def delete_data(self, query: Dict) -> int:
        """Delete documents based on the query and return the count of deleted documents."""
        try:
            delete_result = self.collection.delete_many(query)
            print(f"Deleted {delete_result.deleted_count} documents")
            return delete_result.deleted_count
        except Exception as e:
            print(f"Failed to delete data: {e}")
            return 0


# Usage example
if __name__ == "__main__":
    # MongoDB connection URI and certificate
    uri = "mongodb+srv://guavadb.oingz.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=guavadb"
    cert_file = 'certificates/X509-cert-3512411630284717239.pem'

    # Initialize the MongoDBClient
    mongo_client = MongoDBClient(uri=uri, cert_file=cert_file, db_name='quavadb', collection_name='testCol')

    # Log in to MongoDB
    mongo_client.login()

    # Add a 3D vector
    #vector_data = {"x": 1.2, "y": 2.4, "z": 3.6}
    #mongo_client.add_data(vector_data)

    # Read all documents
    mongo_client.read_data()

    # Delete a document with a specific condition (e.g., x = 1.2)
    #mongo_client.delete_data({"x": 1.2})
