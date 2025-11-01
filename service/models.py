"""Models for Product Demo Service"""
# Copyright 2016, 2023 John J. Rofrano.
# Licensed under the Apache License, Version 2.0

import logging
from enum import Enum
from decimal import Decimal, InvalidOperation
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")
db = SQLAlchemy()


def init_db(app: Flask):
    """Initialize the SQLAlchemy app (proxy for Product.init_db)."""
    Product.init_db(app)


class DataValidationError(Exception):
    """Used for any data validation errors when deserializing."""


class Category(Enum):
    """Enumeration of valid Product Categories"""
    UNKNOWN = 0
    CLOTHS = 1
    FOOD = 2
    HOUSEWARES = 3
    AUTOMOTIVE = 4
    TOOLS = 5


class Product(db.Model):
    """Represents a Product"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    available = db.Column(db.Boolean(), nullable=False, default=True)
    category = db.Column(
        db.Enum(Category), nullable=False, server_default=(Category.UNKNOWN.name)
    )

    def __repr__(self):
        return f"<Product {self.name} id=[{self.id}]>"

    def create(self):
        """Creates this Product in the database."""
        logger.info("Creating %s", self.name)
        self.id = None  # next PK
        db.session.add(self)
        db.session.commit()

    def update(self):
        """Updates this Product in the database."""
        logger.info("Updating %s", self.name)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        db.session.commit()

    def delete(self):
        """Removes this Product from the data store."""
        logger.info("Deleting %s", self.name)
        db.session.delete(self)
        db.session.commit()

    def serialize(self) -> dict:
        """Serializes a Product into a dictionary (robust if category is None)."""
        cat_name = self.category.name if self.category else Category.UNKNOWN.name
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": str(self.price),
            "available": self.available,
            "category": cat_name,
        }

    def deserialize(self, data: dict):
        """Deserializes a Product from a dictionary."""
        try:
            self.name = data["name"]
            self.description = data["description"]

            raw_price = data["price"]
            if isinstance(raw_price, (int, float, Decimal)):
                self.price = Decimal(str(raw_price))
            elif isinstance(raw_price, str):
                self.price = Decimal(raw_price.strip())
            else:
                raise DataValidationError(
                    "Invalid type for price: " + str(type(raw_price))
                )

            if isinstance(data["available"], bool):
                self.available = data["available"]
            else:
                raise DataValidationError(
                    "Invalid type for boolean [available]: "
                    + str(type(data["available"]))
                )

            self.category = getattr(Category, data["category"])
        except InvalidOperation as error:
            raise DataValidationError("Invalid price value") from error
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid product: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid product: body of request contained bad or no data "
                + str(error)
            ) from error
        return self

    @classmethod
    def init_db(cls, app: Flask):
        """Initializes the database session (idempotent)."""
        logger.info("Initializing database")
        # prevent re-initializing after first request
        if not app.config.get("DB_INITED", False):
            db.init_app(app)
            app.config["DB_INITED"] = True
        app.app_context().push()
        db.create_all()

    @classmethod
    def all(cls) -> list:
        logger.info("Processing all Products")
        return cls.query.all()

    @classmethod
    def find(cls, product_id: int):
        logger.info("Processing lookup for id %s ...", product_id)
        return cls.query.get(product_id)

    @classmethod
    def find_by_name(cls, name: str) -> list:
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name).all()

    @classmethod
    def find_by_price(cls, price: Decimal) -> list:
        logger.info("Processing price query for %s ...", price)
        price_value = price
        if isinstance(price, str):
            price_value = Decimal(price.strip(' "'))
        elif isinstance(price, (int, float)):
            price_value = Decimal(str(price))
        return cls.query.filter(cls.price == price_value).all()

    @classmethod
    def find_by_availability(cls, available: bool = True) -> list:
        logger.info("Processing available query for %s ...", available)
        return cls.query.filter(cls.available == available).all()

    @classmethod
    def find_by_category(cls, category: Category = Category.UNKNOWN) -> list:
        logger.info("Processing category query for %s ...", category.name)
        return cls.query.filter(cls.category == category).all()
