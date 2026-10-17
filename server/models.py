from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.ext.associationproxy import association_proxy
from marshmallow import Schema, fields


# Define a naming convention for foreign key constraints
# This ensures consistent constraint names across database migrations
metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

# Initialize SQLAlchemy with the custom metadata configuration.
db = SQLAlchemy(metadata=metadata)


class Customer(db.Model):
    """
    Represents a customer in the e-commerce database.

    A customer can write multiple reviews and access the items
    they have reviewed through an association proxy

    Attributes:
        id (int): Unique identifier for the customer
        name (str): Customer's name
        reviews: Collection of reviews written by the customer
        items: Association proxy providing access to reviewed items
    """

    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    reviews = db.relationship('Review', back_populates="customer")
    items = association_proxy("reviews", "item")

    def __repr__(self):
        """Return a readable representation of the customer"""
        return f'<Customer {self.id}, {self.name}>'



class Item(db.Model):
    """
    Represents an item available in the e-commerce database

    Each item can be associated with multiple customer reviews

    Attributes:
        id (int): Unique identifier for the item
        name (str): Name of the item
        price (float): Price of the item
        reviews: Collection of reviews associated with the item
    """

    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    price = db.Column(db.Float)

    # Establish a one-to-many relationship with Review
    reviews = db.relationship('Review', back_populates="item")

    def __repr__(self):
        """Return a readable representation of the item"""
        return f'<Item {self.id}, {self.name}, {self.price}>'


class Review(db.Model):
    """
    Represents a review written by a customer for an item

    Acts as an association model connecting Customer and Item
    through foreign keys and bidirectional relationships

    Attributes:
        id (int): Unique identifier for the review
        comment (str): Written review of the item
        customer_id (int): Foreign key referencing customers.id
        item_id (int): Foreign key referencing items.id
        customer: Customer associated with the review
        item: Item associated with the review
    """

    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String)
    
    # Foreign keys connect each review to a customer and an item
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))

    # Establish the reciprocal relationships with Customer and Item
    customer = db.relationship('Customer', back_populates='reviews')
    item = db.relationship('Item', back_populates='reviews')

# ---------------------------------------------------------
# Marshmallow Serialization Schemas
# ---------------------------------------------------------
# Convert SQLAlchemy model instances into dictionaries
# Nested relationships allow related data to be serialized
# Exclusions prevent circular references and recursion errors

class CustomerSchema(Schema):
    """
    Serializes Customer objects into dictionary representations

    Includes customer attributes, associated reviews, and reviewed
    items. Nested relationships exclude fields that could introduce
    circular references
    """

    id = fields.Integer()
    name = fields.String()

    # Include multiple reviews without recursively nesting their
    # associated customer and item objects.
    reviews = fields.Nested('ReviewSchema', many=True, exclude=("customer", "item"))

    # Serialize reviewed items through the association proxy.
    # Exclude item reviews to prevent recursive serialization
    items = fields.Nested('ItemSchema', many=True, exclude=("reviews",))

class ItemSchema(Schema):
    """
    Serializes Item objects into dictionary representations

    Includes the item's attributes and associated reviews while
    excluding nested relationships that could cause recursion
    """

    id = fields.Integer()
    name = fields.String()
    price = fields.Float()

    # Include reviews without recursively nesting customer or item
    reviews = fields.Nested("ReviewSchema", many=True, exclude=("customer", "item"))

class ReviewSchema(Schema):
    """
    Serializes Review objects into dictionary representations

    Includes review attributes and nested customer and item data
    Foreign key columns are intentionally omitted because related
    objects are represented through nested schemas

    Nested exclusions prevent circular references between models
    """
    id = fields.Integer()
    comment = fields.String()

    # Include customer details without nesting reviews or items
    customer = fields.Nested('CustomerSchema', exclude=("reviews", "items"))

    # Include item details without recursively nesting reviews
    item = fields.Nested('ItemSchema', exclude=("reviews",))