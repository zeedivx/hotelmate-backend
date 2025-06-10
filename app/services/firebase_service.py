import json
import os
from typing import Dict, List, Optional, Any
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings


class FirebaseService:
    _instance = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._db is None:
            self.initialize_firebase()

    def initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self._db = firestore.client()
                print("✅ Using existing Firebase connection")
                return

            # Initialize Firebase with credentials
            if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                # Use service account file
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred, {
                    'projectId': settings.FIREBASE_PROJECT_ID
                })
                print(f"✅ Firebase initialized with credentials file")
            else:
                # Use default credentials (for local development)
                firebase_admin.initialize_app()
                print(f"✅ Firebase initialized with default credentials")

            self._db = firestore.client()
            print(f"🔥 Connected to Firestore: {settings.FIREBASE_PROJECT_ID}")

        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            raise

    @property
    def db(self):
        """Get Firestore database instance"""
        if self._db is None:
            self.initialize_firebase()
        return self._db

    # Collection helpers
    def get_collection(self, collection_name: str):
        """Get a Firestore collection reference"""
        return self.db.collection(collection_name)

    def get_users_collection(self):
        """Get users collection"""
        return self.get_collection(settings.USERS_COLLECTION)

    def get_hotels_collection(self):
        """Get hotels collection"""
        return self.get_collection(settings.HOTELS_COLLECTION)

    def get_rooms_collection(self):
        """Get rooms collection"""
        return self.get_collection(settings.ROOMS_COLLECTION)

    def get_reservations_collection(self):
        """Get reservations collection"""
        return self.get_collection(settings.RESERVATIONS_COLLECTION)

    # CRUD operations
    async def create_document(self, collection_name: str, data: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """Create a new document in collection"""
        try:
            collection = self.get_collection(collection_name)
            if doc_id:
                doc_ref = collection.document(doc_id)
                doc_ref.set(data)
                return doc_id
            else:
                doc_ref = collection.add(data)[1]
                return doc_ref.id
        except Exception as e:
            print(f"❌ Error creating document: {e}")
            raise

    async def get_document(self, collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        try:
            doc_ref = self.get_collection(collection_name).document(doc_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
        except Exception as e:
            print(f"❌ Error getting document: {e}")
            raise

    async def update_document(self, collection_name: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update a document"""
        try:
            doc_ref = self.get_collection(collection_name).document(doc_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            print(f"❌ Error updating document: {e}")
            raise

    async def delete_document(self, collection_name: str, doc_id: str) -> bool:
        """Delete a document"""
        try:
            doc_ref = self.get_collection(collection_name).document(doc_id)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            raise

    async def get_documents(self, collection_name: str, limit: Optional[int] = None,
                            where_clauses: Optional[List] = None) -> List[Dict[str, Any]]:
        """Get multiple documents from collection"""
        try:
            query = self.get_collection(collection_name)

            # Apply where clauses
            if where_clauses:
                for clause in where_clauses:
                    query = query.where(clause[0], clause[1], clause[2])

            # Apply limit
            if limit:
                query = query.limit(limit)

            docs = query.stream()
            result = []

            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                result.append(data)

            return result
        except Exception as e:
            print(f"❌ Error getting documents: {e}")
            raise

    async def document_exists(self, collection_name: str, doc_id: str) -> bool:
        """Check if document exists"""
        try:
            doc_ref = self.get_collection(collection_name).document(doc_id)
            doc = doc_ref.get()
            return doc.exists
        except Exception as e:
            print(f"❌ Error checking document existence: {e}")
            return False

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        try:
            users = await self.get_documents(
                settings.USERS_COLLECTION,
                limit=1,
                where_clauses=[('email', '==', email)]
            )
            return users[0] if users else None
        except Exception as e:
            print(f"❌ Error getting user by email: {e}")
            raise


# Create singleton instance
firebase_service = FirebaseService()