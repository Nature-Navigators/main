# Contains all the necessary database models

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
from sqlalchemy import Float


class Base(SerializerMixin, DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# many-to-many follower table
secondary_following = db.Table(
    'user_following', Base.metadata,
    db.Column("followedBy_id", db.Uuid, db.ForeignKey("user_table.userID"), primary_key=True),
    db.Column("following_id", db.Uuid, db.ForeignKey("user_table.userID"), primary_key=True),
)


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

    # prevent recursion
    serialize_rules = ('-posts.user.posts', '-profileImage.user', '-savedEvents.user', '-createdEvents.user', '-following', '-followedBy')

    #relationships:
    #   back_populates: establishes that the one-to-many is also a many-to-one
    #   lazy = selectin means that it uses the primary keys and multiple select statements
    #   lazy = joined means it joins the tables on select
    #   online i've read that selectin is good for many-to-many & one-to-many and joined is good for many-to-one
    posts:Mapped[List["Post"]] = relationship('Post', back_populates='user', lazy='selectin') # m
    comments = db.relationship('Comment', back_populates='user', lazy='selectin') # m
    createdEvents = db.relationship('Event', back_populates='creator', lazy='selectin') # m
    savedEvents = db.relationship('Favorite', back_populates='user', lazy='selectin') 
    profileImage:Mapped["ProfileImage"] = relationship(back_populates='user', lazy='selectin')
    
    following: Mapped[List["User"]] = relationship (
        "User",
        secondary = secondary_following,
        primaryjoin= userID == secondary_following.c.followedBy_id,
        secondaryjoin= userID == secondary_following.c.following_id,
        back_populates= "followedBy"
    )

    followedBy: Mapped[List["User"]] = relationship (
        "User",
        secondary= secondary_following,
        primaryjoin= userID == secondary_following.c.following_id,
        secondaryjoin= userID == secondary_following.c.followedBy_id,
        back_populates="following"
    )

    liked_posts: Mapped[List["PostLike"]] = relationship('PostLike', back_populates='user', lazy='selectin')
    
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

    @property
    def serialize(self):
        return {
            'userID': str(self.userID),
            'username': self.username,
            'email': self.email,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'bio': self.bio,
            'pronouns': self.pronouns,
            'posts': [post.serialize for post in self.posts],
            'createdEvents': [event.to_dict() for event in self.createdEvents],
            'savedEvents': [favorite.to_dict() for favorite in self.savedEvents],
            'profileImage': self.profileImage.serialize if self.profileImage else None,
            'following': [user.serialize for user in self.following],
            'followedBy': [user.serialize for user in self.followedBy],
            'liked_posts': [like.serialize for like in self.liked_posts]
        }

class Post(Base, UserMixin):
    __tablename__ = "post_table"
    postID:Mapped[uuid.UUID] = mapped_column(primary_key=True)
    caption:Mapped[str] = mapped_column(nullable=True)
    likes:Mapped[List["PostLike"]] = relationship('PostLike', back_populates='post', cascade="all, delete", passive_deletes=True)
    likes_count:Mapped[int] = mapped_column(nullable=False, default=0)  # Correctly define likes_count column
    birdID:Mapped[str] = mapped_column(nullable=False, default="unidentified birdie")
    locationID:Mapped[str] = mapped_column(nullable=False, default="unknown location")
    datePosted:Mapped[datetime.datetime] = mapped_column(nullable=True)
    serialize_rules = ('-images.post',)
    userID:Mapped[uuid.UUID] = mapped_column(db.ForeignKey("user_table.userID"), nullable=False)
    user:Mapped["User"] = relationship('User', back_populates='posts', lazy='joined') # o
    comments = db.relationship('Comment', back_populates='post', lazy='selectin') # m
    images: Mapped[List["PostImage"]] = relationship(back_populates='post', cascade="all, delete", passive_deletes=True)

    @property
    def serialize(self):
        return {
            'postID': str(self.postID),
            'caption': self.caption,
            'likes_count': self.likes_count,
            'birdID': self.birdID,
            'locationID': self.locationID,
            'datePosted': self.datePosted.isoformat() if self.datePosted else None,
            'userID': str(self.userID),
            'user': self.user.serialize,  # Include the user attribute
            'images': [image.serialize for image in self.images]
        }

class Event(Base):
    __tablename__ = "event_table"
    eventID = db.Column(db.Uuid, primary_key=True)
    eventDate = db.Column(db.DateTime(timezone=True), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(256))
    location = db.Column(db.String(150)) #may need to change
    latitude = db.Column(Float, nullable=True)
    longitude = db.Column(Float, nullable=True) 

    userID = db.Column(db.Uuid, db.ForeignKey("user_table.userID"))

    creator = db.relationship('User', back_populates='createdEvents', lazy='joined') #o
    favorited_by = db.relationship('Favorite', back_populates='event', lazy='selectin') 

    serialize_rules = ('-creator', '-favorited_by', '-images')

    images: Mapped[List["EventImage"]] = relationship(back_populates='event', cascade="all, delete", passive_deletes=True)

    def to_dict(self):
        return {
            'eventID': self.eventID,
            'title': self.title,
            'eventDate': self.eventDate.strftime('%Y-%m-%d %H:%M'), 
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'userID': self.userID,
            'images': [image.to_dict() for image in self.images]
        }

    def __repr__(self):
        return f'<Event {self.title}>'


class Favorite(Base, db.Model):
    __tablename__ = 'favorite_table'
    id = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Uuid, db.ForeignKey('user_table.userID'), nullable=False)
    eventID = db.Column(db.Uuid, db.ForeignKey('event_table.eventID'), nullable=False)
    
    # relationships to User and Event for back references
    user = db.relationship('User', back_populates='savedEvents', lazy='joined')
    event = db.relationship('Event', back_populates='favorited_by', lazy='joined')

    serialize_rules = ('-user', '-event')

    __table_args__ = (
        db.UniqueConstraint('userID', 'eventID', name='unique_user_event_pair'),
    ) 

    def to_dict(self):
        return {}

    @property
    def serialize(self):
        return {
            'id': self.id,
            'userID': str(self.userID),
            'eventID': str(self.eventID)
        }

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


class EventImage(Image):
    __tablename__ = "eventimage_table"
    imageID: Mapped[uuid.UUID] = mapped_column(db.ForeignKey("image_table.imageID"), primary_key=True)
    eventID: Mapped[uuid.UUID] = mapped_column(db.ForeignKey("event_table.eventID", ondelete="CASCADE"), nullable=False)

    event: Mapped["Event"] = relationship(back_populates="images")
    __mapper_args__ = {
        "polymorphic_identity": "event_image"
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

    @property
    def serialize(self):
        return {
            'imageID': str(self.imageID),
            'name': self.name,
            'imagePath': self.imagePath,
            'altText': self.altText,
            'userID': str(self.userID)
        }

class PostLike(Base):
    __tablename__ = 'post_like_table'
    id = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Uuid, db.ForeignKey('user_table.userID'), nullable=False)
    postID = db.Column(db.Uuid, db.ForeignKey('post_table.postID'), nullable=False)

    # relationships to User and Post for back references
    user = db.relationship('User', back_populates='liked_posts', lazy='joined')
    post = db.relationship('Post', back_populates='likes', lazy='joined')

    # unique to prevent duplicates
    __table_args__ = (
        db.UniqueConstraint('userID', 'postID', name='unique_user_post_like'),
    )

    serialize_rules = ('-user', '-post')

    @property
    def serialize(self):
        return {
            'id': self.id,
            'userID': str(self.userID),
            'postID': str(self.postID)
        }

class Comment(Base):
    __tablename__ = 'comment_table'
    commentID = db.Column(db.Uuid, primary_key=True)
    text = db.Column(db.String(256), nullable=False)
    dateCommented = db.Column(db.DateTime(timezone=True), nullable=False)

    postID = db.Column(db.Uuid, db.ForeignKey('post_table.postID'), nullable=False)
    username = db.Column(db.String, db.ForeignKey('user_table.username'), nullable=False)  

    user = db.relationship('User', back_populates='comments', lazy='joined', foreign_keys=[username])
    post = db.relationship('Post', back_populates='comments', lazy='joined')

    serialize_rules = ('-user', '-post')
    @property
    def serialize(self):
        return {
            'commentID': str(self.commentID),
            'text': self.text,
            'dateCommented': self.dateCommented.isoformat(),
            'postID': str(self.postID),
            'username': self.username  
        }

