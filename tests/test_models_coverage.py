"""Extra coverage for service.models"""
# pylint: disable=missing-class-docstring,too-few-public-methods

import unittest
from decimal import Decimal

from service import app
from service.models import Product, Category, DataValidationError, db


class TestModelsCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True

    def setUp(self):
        self.client = app.test_client()
        # fresh table
        with app.app_context():
            db.session.query(Product).delete()
            db.session.commit()

    def test_serialize_handles_none_category(self):
        """If category is None, serialize should use UNKNOWN"""
        p = Product(
            name="widget",
            description="desc",
            price=Decimal("9.99"),
            available=True,
        )
        # not persisted => allow None
        p.category = None
        data = p.serialize()
        self.assertEqual(data["category"], "UNKNOWN")

    def test_deserialize_success(self):
        payload = {
            "name": "hammer",
            "description": "tool",
            "price": "12.50",
            "available": True,
            "category": "TOOLS",
        }
        p = Product().deserialize(payload)
        self.assertEqual(p.name, "hammer")
        self.assertEqual(p.category, Category.TOOLS)
        self.assertEqual(str(p.price), "12.50")

    def test_deserialize_missing_field_raises(self):
        payload = {
            # "name" missing
            "description": "tool",
            "price": "12.50",
            "available": True,
            "category": "TOOLS",
        }
        with self.assertRaises(DataValidationError):
            Product().deserialize(payload)

    def test_deserialize_bad_available_type(self):
        payload = {
            "name": "hammer",
            "description": "tool",
            "price": "12.50",
            "available": "yes",  # not bool
            "category": "TOOLS",
        }
        with self.assertRaises(DataValidationError):
            Product().deserialize(payload)

    def test_deserialize_bad_price(self):
        payload = {
            "name": "hammer",
            "description": "tool",
            "price": "twelve.fifty",  # invalid decimal
            "available": True,
            "category": "TOOLS",
        }
        with self.assertRaises(DataValidationError):
            Product().deserialize(payload)

    def test_deserialize_bad_category_attribute(self):
        payload = {
            "name": "hammer",
            "description": "tool",
            "price": "12.50",
            "available": True,
            "category": "NOT_A_REAL_CATEGORY",
        }
        with self.assertRaises(DataValidationError):
            Product().deserialize(payload)

    def test_update_raises_without_id(self):
        p = Product(
            name="x",
            description="y",
            price=Decimal("1.00"),
            available=True,
            category=Category.UNKNOWN,
        )
        with self.assertRaises(DataValidationError):
            p.update()

    def test_crud_and_finders(self):
        with app.app_context():
            a = Product(
                name="tee",
                description="shirt",
                price=Decimal("19.99"),
                available=True,
                category=Category.CLOTHS,
            )
            b = Product(
                name="tee",
                description="spare",
                price=Decimal("21.00"),
                available=False,
                category=Category.CLOTHS,
            )
            c = Product(
                name="hammer",
                description="tool",
                price=Decimal("12.50"),
                available=True,
                category=Category.TOOLS,
            )
            for p in (a, b, c):
                p.create()

            self.assertEqual(len(Product.all()), 3)

            found = Product.find(a.id)
            self.assertIsNotNone(found)
            self.assertEqual(found.name, "tee")

            by_name = Product.find_by_name("tee")
            self.assertTrue(all(p.name == "tee" for p in by_name))

            by_price = Product.find_by_price(Decimal("12.50"))
            self.assertTrue(all(str(p.price) == "12.50" for p in by_price))

            by_avail = Product.find_by_availability(True)
            self.assertTrue(all(p.available for p in by_avail))

            by_cat = Product.find_by_category(Category.TOOLS)
            self.assertTrue(all(p.category == Category.TOOLS for p in by_cat))

            # delete one, ensure count drops
            c.delete()
            self.assertEqual(len(Product.all()), 2)
