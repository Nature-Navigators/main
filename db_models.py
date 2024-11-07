from db import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask import current_app 
import uuid
import datetime
from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from sqlalchemy import ForeignKey


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

    serialize_rules = ('-posts.user.posts','-profileImage.user', '-savedEvents.user', '-createdEvents.creator')

    #relationships:
    #   back_populates: establishes that the one-to-many is also a many-to-one
    #   lazy = selectin means that it uses the primary keys and multiple select statements
    #   lazy = joined means it joins the tables on select
    #   online i've read that selectin is good for many-to-many & one-to-many and joined is good for many-to-one
    posts:Mapped[List["Post"]] = relationship('Post', back_populates='user', lazy='selectin') # m
    #comments = db.relationship('Comment', back_populates='user', lazy='selectin') # m
    createdEvents = db.relationship('Event', back_populates='creator', lazy='selectin') # m
    #savedEvents = db.relationship('Event', secondary=savedBy, back_populates='usersSaved') # m
    savedEvents = db.relationship('Favorite', back_populates='user', lazy='selectin') 
    profileImage:Mapped["ProfileImage"] = relationship(back_populates='user', lazy='selectin')

    def get_id(self):
        return self.userID
    
    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'userID': str(self.userID)})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            userID = uuid.UUID(s.loads(token)['userID'])
        except:
            return None
        return db.session.query(User).get(userID)

class Post(Base):
    __tablename__ = "post_table"
    postID:Mapped[uuid.UUID] = mapped_column(primary_key=True)
    caption:Mapped[str] = mapped_column(nullable=True)
    datePosted:Mapped[datetime.datetime] = mapped_column(nullable=True)

    serialize_rules = ('-images.post',)


    # relationships + foreign keys
    userID:Mapped[uuid.UUID] = mapped_column(db.ForeignKey("user_table.userID"), nullable=False)
    user:Mapped["User"] = relationship('User', back_populates='posts', lazy='joined') # o
    #comments = db.relationship('Comment', back_populates='post', lazy='selectin') # m
    images: Mapped[List["PostImage"]] = relationship(back_populates='post', cascade="all, delete", passive_deletes=True)

# class Comment(db.Model):
#     __tablename__ = "comment_table"
#     dateCommented = db.Column(db.DateTime(timezone=True))
#     text = db.Column(db.String(256))

#     # relationships + foreign keys
#     userID = db.Column(db.Uuid, db.ForeignKey("user_table.userID"), primary_key=True)
#     postID = db.Column(db.Uuid, db.ForeignKey("post_table.postID"), primary_key=True)

#     user = db.relationship('User', back_populates='comments', lazy='joined') # o
#     post = db.relationship('Post', back_populates='comments', lazy='joined') # o


class Event(db.Model):
    __tablename__ = "event_table"
    eventID = db.Column(db.Uuid, primary_key=True)
    #datePosted = db.Column(db.DateTime(timezone=True))
    eventDate = db.Column(db.DateTime(timezone=True), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(256))
    location = db.Column(db.String(150)) #may need to change

    userID = db.Column(db.Uuid, db.ForeignKey("user_table.userID"))

    creator = db.relationship('User', back_populates='createdEvents', lazy='joined') #o
    #usersSaved = db.relationship('User', secondary=savedBy, back_populates='savedEvents') #m
    favorited_by = db.relationship('Favorite', back_populates='event', lazy='selectin') 


    def to_dict(self):
        return {
            'eventID': self.eventID,
            'title': self.title,
            'eventDate': self.eventDate.strftime('%Y-%m-%d %H:%M'), 
            'location': self.location,
            'description': self.description,
            'userID': self.userID
        }

    def __repr__(self):
        return f'<Event {self.title}>'


class Favorite(db.Model):
    __tablename__ = 'favorite_table'
    id = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Uuid, db.ForeignKey('user_table.userID'), nullable=False)
    eventID = db.Column(db.Uuid, db.ForeignKey('event_table.eventID'), nullable=False)
    
    # relationships to User and Event for back references
    user = db.relationship('User', back_populates='savedEvents', lazy='joined')
    event = db.relationship('Event', back_populates='favorited_by', lazy='joined')

    __table_args__ = (
        db.UniqueConstraint('userID', 'eventID', name='unique_user_event_pair'),
    ) #ensure no duplicates


# base image class
class Image(Base):
    __tablename__ = "image_table"
    imageID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name:Mapped[str] = mapped_column(nullable=False)
    imagePath: Mapped[str] = mapped_column(nullable=False)
    altText: Mapped[str] = mapped_column(nullable=True)
    type: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": "image",
        "polymorphic_on": "type"
    }

class PostImage(Image):
    __tablename__ = "postimage_table"
    imageID: Mapped[uuid.UUID] = mapped_column(db.ForeignKey("image_table.imageID"), primary_key=True)
    postID: Mapped[uuid.UUID] = mapped_column(db.ForeignKey("post_table.postID", ondelete="CASCADE"), nullable=False)

    post: Mapped["Post"] = relationship(back_populates="images")
    __mapper_args__ = {
        "polymorphic_identity": "post_image"
    }

class ProfileImage(Image):
    __tablename__ = "profileimage_table"
    imageID: Mapped[uuid.UUID] = mapped_column(db.ForeignKey("image_table.imageID"), primary_key=True)
    userID: Mapped[uuid.UUID] = mapped_column(db.ForeignKey("user_table.userID"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="profileImage")
    __mapper_args__ = {
        "polymorphic_identity": "profile_image"
    }