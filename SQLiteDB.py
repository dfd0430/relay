from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Table, MetaData
from sqlalchemy.orm import sessionmaker

class SQLiteDB:
    def __init__(self, db_path="sqlite:///example.db"):
        self.engine = create_engine(db_path, echo=False)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create_table(self, table_name, columns):
        cols = [Column(name, col_type, primary_key=(name == "id")) for name, col_type in columns]
        table = Table(table_name, self.metadata, *cols)
        self.metadata.create_all(self.engine)
        return table

    def insert(self, table, values):
        from sqlalchemy import insert
        stmt = insert(table)
        with self.engine.begin() as conn:
            conn.execute(stmt, values)

    def select_all(self, table):
        from sqlalchemy import select
        stmt = select(table)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]
