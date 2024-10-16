from db import db

# many-to-many association table connecting event & user
savedBy = db.Table(
    "savedBy",
    db.Model.metadata,
    db.Column("userID", db.ForeignKey("user_table.userID"), primary_key=True),
    db.Column("eventID", db.ForeignKey("event_table.eventID"), primary_key=True)
)

class User(db.Model):
    __tablename__ = "user_table"
    userID = db.Column(db.Uuid, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(320), nullable=False)
    #TODO: security?
    password = db.Column(db.String(100), nullable=False)
    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100))
    bio = db.Column(db.String(250))
    pronouns = db.Column(db.String(50))

    #relationships:
    #   back_populates: establishes that the one-to-many is also a many-to-one
    #   lazy = selectin means that it uses the primary keys and multiple select statements
    #   lazy = joined means it joins the tables on select
    #   online i've read that selectin is good for many-to-many & one-to-many and joined is good for many-to-one
    posts = db.relationship('Post', back_populates='user', lazy='selectin') # m
    comments = db.relationship('Comment', back_populates='user', lazy='selectin') # m
    createdEvents = db.relationship('Event', back_populates='creator', lazy='selectin') # m
    savedEvents = db.relationship('Event', secondary=savedBy, back_populates='usersSaved') # m

class Post(db.Model):
    __tablename__ = "post_table"
    postID = db.Column(db.Uuid, primary_key=True)
    caption = db.Column(db.String(512))
    datePosted = db.Column(db.DateTime(timezone=True))

    # relationships + foreign keys
    userID = db.Column(db.Uuid, db.ForeignKey("user_table.userID"))
    user = db.relationship('User', back_populates='posts', lazy='joined') # o
    comments = db.relationship('Comment', back_populates='post', lazy='selectin') # m


class Comment(db.Model):
    __tablename__ = "comment_table"
    dateCommented = db.Column(db.DateTime(timezone=True))
    text = db.Column(db.String(256))

    # relationships + foreign keys
    userID = db.Column(db.Uuid, db.ForeignKey("user_table.userID"), primary_key=True)
    postID = db.Column(db.Uuid, db.ForeignKey("post_table.postID"), primary_key=True)

    user = db.relationship('User', back_populates='comments', lazy='joined') # o
    post = db.relationship('Post', back_populates='comments', lazy='joined') # o


class Event(db.Model):
    __tablename__ = "event_table"
    eventID = db.Column(db.Uuid, primary_key=True)
    datePosted = db.Column(db.DateTime(timezone=True))
    eventDate = db.Column(db.DateTime(timezone=True), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(256))

    #relationships + foreign keys
    userID = db.Column(db.Uuid, db.ForeignKey("user_table.userID"))

    creator = db.relationship('User', back_populates='createdEvents', lazy='joined') #o
    usersSaved = db.relationship('User', secondary=savedBy, back_populates='savedEvents') #m


#TODO: images

#TODO: delete me
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return "Hello world, my name is %r" % self.name
    