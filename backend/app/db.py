import os
import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_FILE = os.environ.get("PRODUCT_DB_FILE", str(BASE_DIR / "products.db"))

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    size TEXT NOT NULL DEFAULT '',
    material TEXT NOT NULL DEFAULT '',
    sku TEXT NOT NULL UNIQUE
);
"""

PRODUCT_COLUMNS = ["name", "description", "quantity", "price", "category", "color", "size", "material", "sku"]

DEFAULT_PRODUCTS = [
    ("Camiseta", "Camiseta de algodao 100% com estampa exclusiva", 12, 49.90, "Vestuario", "Preta", "P", "Algodao", "CAM-PT-P"),
    ("Camiseta", "Camiseta de algodao 100% com estampa exclusiva", 28, 49.90, "Vestuario", "Preta", "M", "Algodao", "CAM-PT-M"),
    ("Camiseta", "Camiseta de algodao 100% com estampa exclusiva", 17, 49.90, "Vestuario", "Preta", "G", "Algodao", "CAM-PT-G"),
    ("Tenis", "Tenis esportivo para uso diario e treinos leves", 8, 199.90, "Calcados", "Branco", "38", "Couro sintetico e borracha", "TEN-BR-38"),
    ("Tenis", "Tenis esportivo para uso diario e treinos leves", 14, 199.90, "Calcados", "Branco", "40", "Couro sintetico e borracha", "TEN-BR-40"),
    ("Tenis", "Tenis esportivo para uso diario e treinos leves", 10, 199.90, "Calcados", "Branco", "42", "Couro sintetico e borracha", "TEN-BR-42"),
    ("Tenis", "Tenis esportivo para uso diario e treinos leves", 5, 199.90, "Calcados", "Preto", "41", "Couro sintetico e borracha", "TEN-PT-41"),
    ("Mochila", "Mochila resistente com varios compartimentos", 9, 129.90, "Acessorios", "Azul marinho", "Unico", "Poliester", "MOC-AZ-UN"),
    ("Mochila", "Mochila resistente com varios compartimentos", 6, 129.90, "Acessorios", "Preta", "Unico", "Poliester", "MOC-PT-UN"),
    ("Calca Jeans", "Calca jeans slim com elastano", 11, 159.90, "Vestuario", "Azul", "40", "Jeans com elastano", "CAL-AZ-40"),
    ("Calca Jeans", "Calca jeans slim com elastano", 18, 159.90, "Vestuario", "Azul", "42", "Jeans com elastano", "CAL-AZ-42"),
    ("Calca Jeans", "Calca jeans slim com elastano", 7, 159.90, "Vestuario", "Azul", "44", "Jeans com elastano", "CAL-AZ-44"),
    ("Jaqueta", "Jaqueta corta-vento leve com capuz", 4, 229.90, "Vestuario", "Verde", "M", "Nylon", "JAQ-VD-M"),
    ("Jaqueta", "Jaqueta corta-vento leve com capuz", 7, 229.90, "Vestuario", "Verde", "G", "Nylon", "JAQ-VD-G"),
    ("Bone", "Bone ajustavel com bordado frontal", 22, 39.90, "Acessorios", "Vermelho", "Unico", "Algodao", "BON-VM-UN"),
    ("Relogio", "Relogio digital resistente a respingos", 6, 249.90, "Acessorios", "Preto", "Unico", "Silicone e aco inox", "REL-PT-UN"),
    ("Sandalia", "Sandalia casual confortavel para uso diario", 9, 89.90, "Calcados", "Caramelo", "36", "Couro sintetico", "SAN-CA-36"),
    ("Sandalia", "Sandalia casual confortavel para uso diario", 16, 89.90, "Calcados", "Caramelo", "38", "Couro sintetico", "SAN-CA-38"),
    ("Sandalia", "Sandalia casual confortavel para uso diario", 8, 89.90, "Calcados", "Caramelo", "40", "Couro sintetico", "SAN-CA-40"),
]


def get_connection(db_file: str = DEFAULT_DB_FILE) -> sqlite3.Connection:
    conn = sqlite3.connect(db_file, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper()).strip("-")
    return slug or "PRODUTO"


def _table_exists(cursor: sqlite3.Cursor) -> bool:
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'products'")
    return cursor.fetchone() is not None


def _has_unique_name_index(cursor: sqlite3.Cursor) -> bool:
    cursor.execute("PRAGMA index_list(products)")
    indexes = cursor.fetchall()
    for index in indexes:
        if not index["unique"]:
            continue
        cursor.execute(f"PRAGMA index_info({index['name']})")
        columns = [row["name"] for row in cursor.fetchall()]
        if columns == ["name"]:
            return True
    return False


def _needs_schema_migration(cursor: sqlite3.Cursor) -> bool:
    cursor.execute("PRAGMA table_info(products)")
    columns = {row["name"] for row in cursor.fetchall()}
    return not set(PRODUCT_COLUMNS).issubset(columns) or _has_unique_name_index(cursor)


def _migrate_products_schema(cursor: sqlite3.Cursor) -> None:
    cursor.execute("ALTER TABLE products RENAME TO products_old")
    cursor.execute(CREATE_PRODUCTS_TABLE)

    cursor.execute("PRAGMA table_info(products_old)")
    old_columns = {row["name"] for row in cursor.fetchall()}
    select_columns = [column for column in PRODUCT_COLUMNS if column in old_columns]

    if select_columns:
        cursor.execute(f"SELECT {', '.join(select_columns)} FROM products_old")
        for row in cursor.fetchall():
            product = {column: row[column] for column in select_columns}
            name = product.get("name", "Produto")
            size = product.get("size", "Unico") or "Unico"
            color = product.get("color", "Padrao") or "Padrao"
            product.setdefault("description", "")
            product.setdefault("quantity", 0)
            product.setdefault("price", 0)
            product.setdefault("category", "")
            product.setdefault("color", color)
            product.setdefault("size", size)
            product.setdefault("material", "")
            product["sku"] = product.get("sku") or f"{_slug(str(name))}-{_slug(str(color))}-{_slug(str(size))}"

            cursor.execute(
                """
                INSERT OR IGNORE INTO products
                    (name, description, quantity, price, category, color, size, material, sku)
                VALUES
                    (:name, :description, :quantity, :price, :category, :color, :size, :material, :sku)
                """,
                product,
            )

    cursor.execute("DROP TABLE products_old")


def ensure_products_schema(cursor: sqlite3.Cursor) -> None:
    if not _table_exists(cursor):
        cursor.execute(CREATE_PRODUCTS_TABLE)
        return

    if _needs_schema_migration(cursor):
        _migrate_products_schema(cursor)


def init_db(db_file: str = DEFAULT_DB_FILE) -> None:
    conn = get_connection(db_file)
    cursor = conn.cursor()
    ensure_products_schema(cursor)
    cursor.execute(
        """
        DELETE FROM products
        WHERE category = ''
          AND color = ''
          AND size = ''
          AND material = ''
          AND sku LIKE '%PADRAO-UNICO'
        """
    )

    for product in DEFAULT_PRODUCTS:
        cursor.execute(
            """
            INSERT INTO products (name, description, quantity, price, category, color, size, material, sku)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                quantity = excluded.quantity,
                price = excluded.price,
                category = excluded.category,
                color = excluded.color,
                size = excluded.size,
                material = excluded.material
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
        ORDER BY name, color, size
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
        ORDER BY color, size
        LIMIT 1
        """,
        (name.strip(),),
    )
    product = cursor.fetchone()
    conn.close()
    return product
