from pymongo import MongoClient
from bson.objectid import ObjectId
import numpy as np

class VectorDatabase:
    def __init__(self, uri, tls_cert_file):
        self.client = MongoClient(
            uri,
            tls=True,
            tlsCertificateKeyFile=tls_cert_file
        )
        self.db = self.client['quavadb']
        self.collection = self.db['vectorCollection']

    def add_document(self, name, embedding):
        if len(embedding) != 768:
            raise ValueError("Embedding must be 768-dimensional.")
        
        document = {"name": name, "embedding": embedding}
        insert_result = self.collection.insert_one(document)
        return insert_result.inserted_id

    def read_document(self, doc_id=None, name=None):
        query = {}
        if doc_id:
            query["_id"] = ObjectId(doc_id)
        elif name:
            query["name"] = name
        else:
            raise ValueError("Either doc_id or name must be provided.")
        
        return self.collection.find_one(query)

    def find_similar_vectors(self, target_embedding):
        if len(target_embedding) != 768:
            raise ValueError("Target embedding must be 768-dimensional.")

        all_documents = list(self.collection.find({}))
        similarities = []
        
        for doc in all_documents:
            embedding = np.array(doc['embedding'])
            similarity = np.dot(embedding, target_embedding) / (np.linalg.norm(embedding) * np.linalg.norm(target_embedding))
            similarities.append((doc, similarity))
        
        similar_docs = sorted(similarities, key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in similar_docs[:5]]

    def delete_document(self, doc_id=None, name=None):
        query = {}
        if doc_id:
            query["_id"] = ObjectId(doc_id)
        elif name:
            query["name"] = name
        else:
            raise ValueError("Either doc_id or name must be provided.")
        
        result = self.collection.delete_one(query)
        return result.deleted_count
    
# MongoDB connection URI and certificate
uri = "mongodb+srv://guavadb.oingz.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=guavadb"
cert_file = 'certificates/X509-cert-3512411630284717239.pem'

db = VectorDatabase(uri, cert_file)

# Example 768-dimensional embedding
embedding = [0.1] * 768  # Just an example. Replace with actual embedding from Ollama.

# Add a document with a 768-dimensional embedding
db.add_document("Test Document", embedding)

# Find similar vectors
target_embedding = [0.12] * 768  # Example target embedding
similar_docs = db.find_similar_vectors(target_embedding)

print(similar_docs)

for doc in similar_docs:
    print(doc)

delete_document = db.delete_document(name="Test Document")
