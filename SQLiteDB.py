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

    # def create_blueprint_table(self):
    #     """
    #     Creates the blueprint table with the necessary columns.
    #     """
    #     columns = [
    #         ("id", Integer),            # id will be the primary key
    #         ("name", String),           # name column for the blueprint's name
    #         ("obda_file", LargeBinary), # obda_file as a binary field
    #         ("owl_file", LargeBinary),  # owl_file as a binary field
    #         ("properties_file", LargeBinary), # mapping_file as a binary field
    #         ("jdbc_file", LargeBinary), # jdbc_file as a binary field
    #         ("timestamp", DateTime),
    #     ]
    #     # Create the blueprint table using the existing SQLiteDB object
    #     self.create_table("blueprints", columns)
    #
    # def insert_blueprint(self, name, obda_file, owl_file, properties_file, jdbc_file, timestamp):
    #     """
    #     Insert a blueprint into the blueprints table.
    #     """
    #     blueprint_data = {
    #         "name": name,
    #         "obda_file": obda_file,
    #         "owl_file": owl_file,
    #         "properties_file": properties_file,
    #         "jdbc_file": jdbc_file,
    #         "timestamp": timestamp
    #     }
    #
    #     # Insert the blueprint data into the table
    #     table = self.metadata.tables.get("blueprints")
    #
    #     self.insert(table, [blueprint_data])
    #
    # def return_blueprints(self):
    #     table = self.metadata.tables.get("blueprints")
    #     return self.select_all(table)
    #
    # def get_blueprint_by_id(self, blueprint_id):
    #     """
    #     Retrieve a single blueprint by its ID.
    #     """
    #     from sqlalchemy import select
    #     table = self.metadata.tables.get("blueprints")
    #     stmt = select(table).where(table.c.id == blueprint_id)
    #     with self.engine.connect() as conn:
    #         result = conn.execute(stmt).fetchone()
    #         return dict(result._mapping) if result else None

    def create_logs_table(self):
        """
        Creates the logs table in the database with the necessary columns.
        """
        columns = [
            ("id", Integer, True),  # primary key
            ("timestamp", DateTime, False),  # timestamp column
            ("ip", String, False),  # ip column
            ("container_name", String, False),  # container_name column
            ("container_id", String, False),  # new container_id column (using String for IDs)
            ("query", String, False),  # query column
        ]

        table = Table(
            "logs",
            self.metadata,
            *[Column(name, col_type, primary_key=primary_key) for name, col_type, primary_key in columns]
        )
        self.metadata.create_all(self.engine)
        return table

    def insert_log(self, ip, container_name, container_id, query, timestamp):
        """
        Insert a log entry into the logs table.
        """
        log_data = {
            "timestamp": timestamp,
            "ip": ip,
            "container_name": container_name,
            "container_id": container_id,  # include container_id here
            "query": query
        }
        table = self.metadata.tables.get("logs")
        self.insert(table, [log_data])

    def get_logs_by_container(self, container_id):
        """
        Retrieve logs for a specific container by container_id.
        """
        from sqlalchemy import select
        table = self.metadata.tables.get("logs")
        stmt = select(table).where(table.c.container_id == container_id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def get_all_unique_containers(self):
        """
        Returns a list of unique container_id + container_name pairs from logs.
        """
        from sqlalchemy import select, distinct
        table = self.metadata.tables.get("logs")
        stmt = select(
            table.c.container_id,
            table.c.container_name
        ).distinct()

        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]
    ##################################################################################################################################################

    def create_db_connection_table(self):
        """
        Creates the database_connections table for independent DB storage.
        """
        columns = [
            ("id", Integer),  # primary key
            ("name", String),
            ("jdbc_file", LargeBinary),
            ("properties_file", LargeBinary),
            ("timestamp", DateTime),
        ]
        self.create_table("database_connections", columns)

    def insert_db_connection(self, name, jdbc_file, properties_file, timestamp):
        table = self.metadata.tables.get("database_connections")
        data = {
            "name": name,
            "jdbc_file": jdbc_file,
            "properties_file": properties_file,
            "timestamp": timestamp,
        }
        stmt = insert(table).values(**data).returning(table.c.id)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            inserted_id = result.scalar_one()  # fetch the inserted id
        return inserted_id

    def get_all_db_connections(self):
        table = self.metadata.tables.get("database_connections")
        return self.select_all(table)

    def get_db_connection_by_id(self, db_id):
        from sqlalchemy import select
        table = self.metadata.tables.get("database_connections")
        stmt = select(table).where(table.c.id == db_id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return dict(result._mapping) if result else None

    def delete_db_connection(self, db_id):
        """
        Delete a database connection by its ID.
        """
        from sqlalchemy import delete
        table = self.metadata.tables.get("database_connections")
        stmt = delete(table).where(table.c.id == db_id)
        with self.engine.begin() as conn:
            conn.execute(stmt)
##################################################################################################################################################
    def create_obda_configuration_table(self):
        """
        Creates the obda_configurations table for storing OWL and OBDA files.
        """
        columns = [
            ("id", Integer),
            ("name", String),
            ("description", String),  # ← Add this line
            ("owl_file", LargeBinary),
            ("obda_file", LargeBinary),
            ("timestamp", DateTime),
        ]
        self.create_table("obda_configurations", columns)

    def insert_obda_configuration(self, name, description, owl_data, obda_data, timestamp):
        table = self.metadata.tables.get("obda_configurations")
        if table is None:
            raise ValueError("obda_configurations table not found in metadata.")

        data = {
            "name": name,
            "description": description,  # ← Add this line
            "owl_file": owl_data,
            "obda_file": obda_data,
            "timestamp": timestamp,
        }

        stmt = insert(table).values(**data).returning(table.c.id)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            inserted_id = result.scalar_one()

        return inserted_id

    def get_all_obda_configurations(self):
        table = self.metadata.tables.get("obda_configurations")
        return self.select_all(table)

    def get_obda_configuration_by_id(self, obda_id):
        from sqlalchemy import select
        table = self.metadata.tables.get("obda_configurations")
        stmt = select(table).where(table.c.id == obda_id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return dict(result._mapping) if result else None

    def delete_blueprint(self, blueprint_id):
        """
        Delete a blueprint by its ID.
        """
        from sqlalchemy import delete
        table = self.metadata.tables.get("obda_configurations")
        stmt = delete(table).where(table.c.id == blueprint_id)
        with self.engine.begin() as conn:
            conn.execute(stmt)

##################################################################################################################################################
    def create_temp_db_connection_table(self):
        """
        Creates the temp_database_connections table for short-lived DB storage.
        """
        columns = [
            ("id", Integer),  # primary key
            ("name", String),
            ("jdbc_file", LargeBinary),
            ("properties_file", LargeBinary),
            ("timestamp", DateTime),
        ]
        self.create_table("temp_database_connections", columns)

    def insert_temp_db_connection(self, name, jdbc_file, properties_file, timestamp):
        table = self.metadata.tables.get("temp_database_connections")
        data = {
            "name": name,
            "jdbc_file": jdbc_file,
            "properties_file": properties_file,
            "timestamp": timestamp,
        }

        stmt = insert(table).returning(table.c.id)

        with self.engine.begin() as conn:
            result = conn.execute(stmt, [data])
            inserted_id = result.scalar()
            return inserted_id

    def get_all_temp_db_connections(self):
        table = self.metadata.tables.get("temp_database_connections")
        return self.select_all(table)

    def get_temp_db_connection_by_id(self, db_id):
        from sqlalchemy import select
        table = self.metadata.tables.get("temp_database_connections")
        stmt = select(table).where(table.c.id == db_id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return dict(result._mapping) if result else None

    def delete_temp_db_connection(self, db_id):
        """
        Delete a temporary database connection by its ID.
        """
        from sqlalchemy import delete
        table = self.metadata.tables.get("temp_database_connections")
        stmt = delete(table).where(table.c.id == db_id)
        with self.engine.begin() as conn:
            conn.execute(stmt)
##################################################################################################################################################

    def create_temp_obda_configuration_table(self):
        """
        Creates the temp_obda_configurations table for temporary storage of OWL and OBDA files.
        """
        columns = [
            ("id", Integer),
            ("name", String),
            ("owl_file", LargeBinary),
            ("obda_file", LargeBinary),
            ("timestamp", DateTime),
        ]
        self.create_table("temp_obda_configurations", columns)



    def insert_temp_obda_configuration(self, name, owl_data, obda_data, timestamp):
        table = self.metadata.tables.get("temp_obda_configurations")
        data = {
            "name": name,
            "owl_file": owl_data,
            "obda_file": obda_data,
            "timestamp": timestamp,
        }
        stmt = insert(table).values(**data).returning(table.c.id)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            inserted_id = result.scalar_one()  # get the inserted id
        return inserted_id

    def get_all_temp_obda_configurations(self):
        table = self.metadata.tables.get("temp_obda_configurations")
        return self.select_all(table)

    def get_temp_obda_configuration_by_id(self, obda_id):
        from sqlalchemy import select
        table = self.metadata.tables.get("temp_obda_configurations")
        stmt = select(table).where(table.c.id == obda_id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return dict(result._mapping) if result else None

    def delete_temp_obda_configuration(self, obda_id):
        from sqlalchemy import delete
        table = self.metadata.tables.get("temp_obda_configurations")
        stmt = delete(table).where(table.c.id == obda_id)
        with self.engine.begin() as conn:
            conn.execute(stmt)


