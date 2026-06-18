from database import engine
from models import Base
from sqlalchemy import inspect, text

print("Database URL:", engine.url)

Base.metadata.create_all(bind=engine)

schema_updates = {
    "bus_passes": {
        "qr_url": "VARCHAR(500) DEFAULT ''",
        "pdf_url": "VARCHAR(500) DEFAULT ''"
    },
    "tickets": {
        "qr_url": "VARCHAR(500) DEFAULT ''",
        "pdf_url": "VARCHAR(500) DEFAULT ''"
    }
}

inspector = inspect(engine)

with engine.begin() as connection:
    for table_name, columns in schema_updates.items():
        existing_columns = {
            column["name"]
            for column in inspector.get_columns(table_name)
        }

        for column_name, column_definition in columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ADD COLUMN {column_name} {column_definition}"
                    )
                )
                print(f"Added {table_name}.{column_name}")

print("Tables created successfully")

print(engine.url)
