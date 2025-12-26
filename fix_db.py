import sqlite3
import os

def update_database():
    # Obtener la ruta absoluta del archivo de base de datos para evitar errores de ruta
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'db.db')
    
    print(f"Conectando a la base de datos en: {db_path}")
    
    if not os.path.exists(db_path):
        print("¡Error! No se encuentra el archivo db.db. Asegúrate de ejecutar este script en la carpeta del proyecto.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Intentar agregar la columna fecha_nacimiento
        print("Intentando agregar columna 'fecha_nacimiento'...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN fecha_nacimiento DATE")
            print("✅ ÉXITO: Columna 'fecha_nacimiento' agregada correctamente.")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("ℹ️ AVISO: La columna 'fecha_nacimiento' ya existía.")
            else:
                print(f"❌ Error al agregar columna: {e}")

        conn.commit()
        conn.close()
        print("\nBase de datos actualizada. Ahora puedes ejecutar 'python app.py'.")
        
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")

if __name__ == '__main__':
    update_database()