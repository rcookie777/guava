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
        if len(embedding) != 1536:
            raise ValueError("Embedding must be 1536-dimensional.")
        
        document = {
            "name": name,
            "embedding": {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1536,
                "similarity": "cosine",
                "values": embedding
            }
        }
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
        """Find documents with embeddings similar to the target using a brute-force approach."""
        # Ensure the target embedding is 1536-dimensional
        if len(target_embedding) != 1536:
            raise ValueError("Target embedding must be 1536-dimensional.")

        # Retrieve all documents from the collection
        all_documents = list(self.collection.find({}))

        # Compute cosine similarities
        similarities = []
        for doc in all_documents:
            # Access the 'values' field of the embedding dictionary
            embedding = np.array(doc['embedding']['values'])  # Extracting values from the dictionary
            # Calculate cosine similarity
            similarity = np.dot(embedding, target_embedding) / (np.linalg.norm(embedding) * np.linalg.norm(target_embedding))
            similarities.append((doc, similarity))
        
        # Sort by similarity
        similar_docs = sorted(similarities, key=lambda x: x[1], reverse=True)

        # Return the top N similar documents (e.g., top 5)
        return [doc for doc, _ in similar_docs[:5]]


    def delete_document(self, doc_id=None, name=None):
        query = {}
        if doc_id:
            query["_id"] = ObjectId(doc_id)
        elif name:
            query["name"] = name
        else:
            raise ValueError("Either doc_id or name must be provided.")
        
        delete_result = self.collection.delete_one(query)
        return delete_result.deleted_count  # Returns the number of documents deleted

# MongoDB connection URI and certificate
uri = "mongodb+srv://guavadb.oingz.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=guavadb"
cert_file = 'storage/certificates/X509-cert-3512411630284717239.pem'

db = VectorDatabase(uri, cert_file)

# Example 1536-dimensional embedding
#embedding = [0.72] * 1536  # Just an example. Replace with actual embedding from Ollama.

# Add a document with a 1536-dimensional embedding
#db.add_document("Test Document", embedding)

#embedding = [0.18] * 1536  # Just an example. Replace with actual embedding from Ollama.
#db.add_document("Test2 Document", embedding)

# Find similar vectors
#target_embedding = [0.5] * 1536  # Example target embedding
#similar_docs = db.find_similar_vectors(target_embedding)

#print(similar_docs)

#for doc in similar_docs:
#    print(type(doc))

#delete_document = db.delete_document(name="Test Document")
