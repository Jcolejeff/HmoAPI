from sqlalchemy.sql import func

def sql_count(query) -> int:
    """
        An efficient alternative to the SQLAlchemy count() function.
        :param: query - SQLAlchemy session query
    """
    count = query.with_entities(func.count()).scalar()
    
    return count