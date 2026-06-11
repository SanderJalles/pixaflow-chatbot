import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_FILE = os.environ.get("PRODUCT_DB_FILE", str(BASE_DIR / "products.db"))

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    size TEXT NOT NULL DEFAULT '',
    material TEXT NOT NULL DEFAULT '',
    sku TEXT NOT NULL DEFAULT ''
);
"""

EXTRA_PRODUCT_COLUMNS = ["category", "color", "size", "material", "sku"]

DEFAULT_PRODUCTS = [
    ("Camiseta", "Camiseta de algodao 100% com estampa exclusiva", 28, 49.90, "Vestuario", "Preta", "M", "Algodao", "CAM-PT-M"),
    ("Tenis", "Tenis esportivo para uso diario e treinos leves", 14, 199.90, "Calcados", "Branco", "40", "Couro sintetico e borracha", "TEN-BR-40"),
    ("Mochila", "Mochila resistente com varios compartimentos", 9, 129.90, "Acessorios", "Azul marinho", "Unico", "Poliester", "MOC-AZ-UN"),
    ("Calca Jeans", "Calca jeans slim com elastano", 18, 159.90, "Vestuario", "Azul", "42", "Jeans com elastano", "CAL-AZ-42"),
    ("Jaqueta", "Jaqueta corta-vento leve com capuz", 7, 229.90, "Vestuario", "Verde", "G", "Nylon", "JAQ-VD-G"),
    ("Bone", "Bone ajustavel com bordado frontal", 22, 39.90, "Acessorios", "Vermelho", "Unico", "Algodao", "BON-VM-UN"),
    ("Relogio", "Relogio digital resistente a respingos", 6, 249.90, "Acessorios", "Preto", "Unico", "Silicone e aco inox", "REL-PT-UN"),
    ("Sandalia", "Sandalia casual confortavel para uso diario", 16, 89.90, "Calcados", "Caramelo", "38", "Couro sintetico", "SAN-CA-38"),
]


def get_connection(db_file: str = DEFAULT_DB_FILE) -> sqlite3.Connection:
    conn = sqlite3.connect(db_file, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_product_columns(cursor: sqlite3.Cursor) -> None:
    cursor.execute("PRAGMA table_info(products)")
    existing_columns = {row["name"] for row in cursor.fetchall()}
    for column in EXTRA_PRODUCT_COLUMNS:
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE products ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")


def init_db(db_file: str = DEFAULT_DB_FILE) -> None:
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute(CREATE_PRODUCTS_TABLE)
    ensure_product_columns(cursor)

    for product in DEFAULT_PRODUCTS:
        cursor.execute(
            """
            INSERT INTO products (name, description, quantity, price, category, color, size, material, sku)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                description = excluded.description,
                quantity = excluded.quantity,
                price = excluded.price,
                category = excluded.category,
                color = excluded.color,
                size = excluded.size,
                material = excluded.material,
                sku = excluded.sku
            """,
            product,
        )

    conn.commit()
    conn.close()


def get_all_products(db_file: str = DEFAULT_DB_FILE) -> list[sqlite3.Row]:
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, description, quantity, price, category, color, size, material, sku
        FROM products
        ORDER BY name
        """
    )
    products = cursor.fetchall()
    conn.close()
    return products


def find_product_by_name(name: str, db_file: str = DEFAULT_DB_FILE) -> sqlite3.Row | None:
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, description, quantity, price, category, color, size, material, sku
        FROM products
        WHERE LOWER(name) = LOWER(?)
        """,
        (name.strip(),),
    )
    product = cursor.fetchone()
    conn.close()
    return product
