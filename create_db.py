from db_init import engine, Base

try:
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")
except Exception as e:
    print("Error during database initialization:", e)
