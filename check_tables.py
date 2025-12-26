from app import app, db

def check_and_create_tables():
    print("Verificando y creando tablas faltantes...")
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tablas verificadas/creadas correctamente.")
            print("Ahora puedes ejecutar 'python app.py' y los colaboradores se guardarán.")
        except Exception as e:
            print(f"❌ Error al crear tablas: {e}")

if __name__ == "__main__":
    check_and_create_tables()