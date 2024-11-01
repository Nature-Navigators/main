from db import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import uuid
import datetime
from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

# many-to-many association table connecting event & user
# savedBy = db.Table(
#     "savedBy",
#     db.Model.metadata,
#     db.Column("userID", db.ForeignKey("user_table.userID"), primary_key=True),
#     db.Column("eventID", db.ForeignKey("event_table.eventID"), primary_key=True)
# )

class Base(SerializerMixin, DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(Base, UserMixin):

    __tablename__ = "user_table"
    userID: Mapped[uuid.UUID] = mapped_column(primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    #TODO: security?
    password: Mapped[str] = mapped_column(nullable=False)
    firstName: Mapped[str] = mapped_column( nullable=True)
    lastName: Mapped[str] = mapped_column( nullable=True)
    bio: Mapped[str] = mapped_column( nullable=True)
    pronouns: Mapped[str] = mapped_column( nullable=True)

    serialize_rules = ('-posts.user',)

    #relationships:
    #   back_populates: establishes that the one-to-many is also a many-to-one
    #   lazy = selectin means that it uses the primary keys and multiple select statements
    #   lazy = joined means it joins the tables on select
    #   online i've read that selectin is good for many-to-many & one-to-many and joined is good for many-to-one
    posts:Mapped[List["Post"]] = relationship('Post', back_populates='user', lazy='selectin') # m
    #comments = db.relationship('Comment', back_populates='user', lazy='selectin') # m
    #createdEvents = db.relationship('Event', back_populates='creator', lazy='selectin') # m
    #savedEvents = db.relationship('Event', secondary=savedBy, back_populates='usersSaved') # m

    def get_id(self):
        return self.userID

class Post(Base):
    __tablename__ = "post_table"
    postID:Mapped[uuid.UUID] = mapped_column(primary_key=True)
    caption:Mapped[str]
    datePosted:Mapped[datetime.datetime]

    # relationships + foreign keys
    userID:Mapped[uuid.UUID] = mapped_column(db.ForeignKey("user_table.userID"), nullable=False)
    user:Mapped["User"] = relationship('User', back_populates='posts', lazy='joined') # o
    #comments = db.relationship('Comment', back_populates='post', lazy='selectin') # m


# class Comment(db.Model):
#     __tablename__ = "comment_table"
#     dateCommented = db.Column(db.DateTime(timezone=True))
#     text = db.Column(db.String(256))

#     # relationships + foreign keys
#     userID = db.Column(db.Uuid, db.ForeignKey("user_table.userID"), primary_key=True)
#     postID = db.Column(db.Uuid, db.ForeignKey("post_table.postID"), primary_key=True)

#     user = db.relationship('User', back_populates='comments', lazy='joined') # o
#     post = db.relationship('Post', back_populates='comments', lazy='joined') # o


# class Event(db.Model):
#     __tablename__ = "event_table"
#     eventID = db.Column(db.Uuid, primary_key=True)
#     datePosted = db.Column(db.DateTime(timezone=True))
#     eventDate = db.Column(db.DateTime(timezone=True), nullable=False)
#     title = db.Column(db.String(150), nullable=False)
#     description = db.Column(db.String(256))

#     #relationships + foreign keys
#     userID = db.Column(db.Uuid, db.ForeignKey("user_table.userID"))

#     creator = db.relationship('User', back_populates='createdEvents', lazy='joined') #o
#     #usersSaved = db.relationship('User', secondary=savedBy, back_populates='savedEvents') #m


#TODO: images

#TODO: delete me
# class Profile(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(200), nullable=False)

#     def __repr__(self):
#         return "Hello world, my name is %r" % self.name
    
    