from fastapi import Depends
from .database import get_db


#
SessionDependency = Depends(get_db)