"""Base CRUD repository with generic create, read, update, delete operations."""

from typing import TypeVar, Generic, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from app.repository.database import Base

T = TypeVar("T", bound=Base)


class BaseCRUD(Generic[T]):
    """
    Generic CRUD repository for database operations.
    
    Usage:
        class UserRepository(BaseCRUD[User]):
            def find_by_email(self, db: Session, email: str) -> Optional[User]:
                return db.query(self.model).filter(self.model.email == email).first()
    """
    
    def __init__(self, model: Type[T]):
        """Initialize repository with model class."""
        self.model = model
    
    def create(self, db: Session, obj_in: Dict[str, Any]) -> T:
        """
        Create a new record in database.
        
        Args:
            db: Database session
            obj_in: Dictionary of data to create
            
        Returns:
            Created model instance
        """
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def read(self, db: Session, id: Any) -> Optional[T]:
        """
        Read a record by ID.
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def read_all(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[T]:
        """
        Read all records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        id: Any, 
        obj_in: Dict[str, Any]
    ) -> Optional[T]:
        """
        Update a record by ID.
        
        Args:
            db: Database session
            id: Primary key value
            obj_in: Dictionary of data to update
            
        Returns:
            Updated model instance or None if not found
        """
        db_obj = self.read(db, id)
        if db_obj:
            for key, value in obj_in.items():
                setattr(db_obj, key, value)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: Any) -> bool:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            True if deleted, False if not found
        """
        db_obj = self.read(db, id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False
    
    def exists(self, db: Session, **filters: Any) -> bool:
        """
        Check if a record exists matching filters.
        
        Args:
            db: Database session
            **filters: Field name and value pairs to filter by
            
        Returns:
            True if record exists, False otherwise
        """
        query = db.query(self.model)
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.first() is not None
