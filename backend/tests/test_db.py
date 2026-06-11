import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import get_all_products, init_db


def test_db_initialization_and_product_seed() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "products_test.db")
        init_db(db_file)
        products = get_all_products(db_file)

        assert len(products) >= 8
        names = [row["name"] for row in products]
        assert "Camiseta" in names
        assert "Tenis" in names
        assert "Mochila" in names

        first_product = dict(products[0])
        assert "category" in first_product
        assert "color" in first_product
        assert "size" in first_product
        assert "material" in first_product
        assert "sku" in first_product
