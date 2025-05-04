from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Table, MetaData, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert


class SQLiteDB:
    def __init__(self, db_path="sqlite:///example.db"):
        self.engine = create_engine(db_path, echo=False)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create_table(self, table_name, columns):
        """
        Creates a table in the database with the provided columns.
        """
        cols = [Column(name, col_type, primary_key=(name == "id")) for name, col_type in columns]
        table = Table(table_name, self.metadata, *cols)
        self.metadata.create_all(self.engine)
        return table

    def insert(self, table, values):
        """
        Insert data into a specific table.
        """
        stmt = insert(table)
        with self.engine.begin() as conn:
            conn.execute(stmt, values)

    def select_all(self, table):
        """
        Select all rows from a specific table.
        """
        from sqlalchemy import select
        stmt = select(table)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def create_blueprint_table(self):
        """
        Creates the blueprint table with the necessary columns.
        """
        columns = [
            ("id", Integer),            # id will be the primary key
            ("name", String),           # name column for the blueprint's name
            ("obda_file", LargeBinary), # obda_file as a binary field
            ("owl_file", LargeBinary),  # owl_file as a binary field
            ("properties_file", LargeBinary), # mapping_file as a binary field
            ("jdbc_file", LargeBinary), # jdbc_file as a binary field
            ("timestamp", DateTime),
        ]
        # Create the blueprint table using the existing SQLiteDB object
        self.create_table("blueprints", columns)

    def insert_blueprint(self, name, obda_file, owl_file, properties_file, jdbc_file, timestamp):
        """
        Insert a blueprint into the blueprints table.
        """
        blueprint_data = {
            "name": name,
            "obda_file": obda_file,
            "owl_file": owl_file,
            "properties_file": properties_file,
            "jdbc_file": jdbc_file,
            "timestamp": timestamp
        }

        # Insert the blueprint data into the table
        table = self.metadata.tables.get("blueprints")

        self.insert(table, [blueprint_data])

    def return_blueprints(self):
        table = self.metadata.tables.get("blueprints")
        return self.select_all(table)

    def get_blueprint_by_id(self, blueprint_id):
        """
        Retrieve a single blueprint by its ID.
        """
        from sqlalchemy import select
        table = self.metadata.tables.get("blueprints")
        stmt = select(table).where(table.c.id == blueprint_id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return dict(result._mapping) if result else None

    def create_logs_table(self):
        """
        Creates the logs table in the database with the necessary columns.
        """
        # Make sure each column tuple contains the name, type, and whether it's a primary key
        columns = [
            ("id", Integer, True),  # id will be the primary key
            ("timestamp", DateTime, False),  # timestamp column
            ("ip", String, False),  # ip column
            ("container_name", String, False),  # container_name column
            ("query", String, False),  # query column
        ]

        # Create the logs table
        table = Table(
            "logs",
            self.metadata,
            *[Column(name, col_type, primary_key=primary_key) for name, col_type, primary_key in columns]
        )
        self.metadata.create_all(self.engine)
        return table

    def insert_log(self, ip, container_name, query, timestamp):
        """
        Insert a log entry into the logs table.
        """
        log_data = {
            "timestamp": timestamp,
            "ip": ip,
            "container_name": container_name,
            "query": query
        }
        table = self.metadata.tables.get("logs")
        self.insert(table, [log_data])

    def get_logs_by_container(self, container_name):
        """
        Retrieve logs for a specific container.
        """
        from sqlalchemy import select
        table = self.metadata.tables.get("logs")
        stmt = select(table).where(table.c.container_name == container_name)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    # Other methods...
