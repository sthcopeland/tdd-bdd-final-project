from decimal import Decimal
import random

import factory
from factory.fuzzy import FuzzyChoice, FuzzyDecimal

from service.models import Product, Category


class ProductFactory(factory.Factory):
    """Factory to create Product objects for tests"""

    class Meta:
        model = Product

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    description = factory.Faker("sentence", nb_words=6)
    price = FuzzyDecimal(1, 999, 2)
    available = FuzzyChoice([True, False])
    category = FuzzyChoice(
        [
            Category.CLOTHS,
            Category.FOOD,
            Category.HOUSEWARES,
            Category.AUTOMOTIVE,
            Category.TOOLS,
        ]
    )


def random_decimal(low: int = 1, high: int = 999) -> Decimal:
    """Helper to produce Decimal values for tests"""
    return Decimal(str(random.randint(low, high)))
