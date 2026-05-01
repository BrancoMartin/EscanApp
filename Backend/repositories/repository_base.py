from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.orm import Session
from Exceptions.InfrastructureError.InfrastructureError import (DatabaseIntegrityError, DatabaseOperationalError, DatabaseProgrammingError
)

#DATABASE INTEGRITY ERROR: UNIQUE constraint, Foreign Key, NOT NULL, Duplicados
# 
#DATABASE OPERATIONAL ERROR: db caida, timeout, conexion rechazada, error de red 
# 
# DATABASE PROGRAMMING ERROR: columna inexistente, tabla inexistente, SQL mal escrito, error en la query

T = TypeVar("T")

class RepositoryBase(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, entity_id: int) -> Optional[T]:
        try:
            return self.session.get(self.model, entity_id)
        except DatabaseIntegrityError as e:
            raise e
        except  DatabaseOperationalError as e:
            raise e
        except DatabaseProgrammingError as e:
            raise e

    def get_all(self) -> List[T]:
        try:
            return self.session.query(self.model).all()
        except DatabaseIntegrityError as e:
            self.session.rollback()
            raise e
        except DatabaseOperationalError as e:
            self.session.rollback()
            raise e
        except DatabaseProgrammingError as e:
            self.session.rollback()
            raise e

    def create(self, entity: T) -> T:

        try:
            self.session.add(entity)
            self.session.commit()
            return entity
        except DatabaseIntegrityError as e:
            self.session.rollback()
            raise e
        except DatabaseOperationalError as e:
            self.session.rollback()
            raise e
        except DatabaseProgrammingError as e:
            self.session.rollback()
            raise e

        

    def delete(self, entity: T) -> None:

        try:
            self.session.delete(entity)
            self.session.commit()
            return entity
        except DatabaseIntegrityError as e: 
            self.session.rollback()
            raise e
        except DatabaseOperationalError as e:
            self.session.rollback()
            raise e
        except DatabaseProgrammingError as e:
            self.session.rollback()
            raise e

        

    def update(self, entity: T) -> T:

        try:
            self.session.merge(entity)
            self.session.commit()
            return entity
        except DatabaseIntegrityError as e:
            self.session.rollback()
            raise e
        except DatabaseOperationalError as e:
            self.session.rollback()
            raise e
        except DatabaseProgrammingError as e:
            self.session.rollback()
            raise e


