from app import db

class Post(db.Model):
    __tablename__='orders'
    id = db.Column(db.Integer,primary_key=True) 
    fname = db.Column(db.String)
    email = db.Column(db.String)
    phone  = db.Column(db.Text(10))
    time = db.Column(db.String)
    location = db.Column(db.String(5))
    orderID = db.Column(db.String(10))
    hauler = db.Column(db.String)
    haulerQuote = db.Column(db.String)    
    customerPrice = db.Column(db.String(10))
    sent_status=db.Column(db.String)
    filename = db.Column(db.String)

    def __init__(self,fname,email,phone,time,location,orderID,hauler,haulerQuote,customerPrice,sent_status,filename):
        #self.id = id
        self.fname = fname
        self.email = email 
        self.phone = phone 
        self.time = time 
        self.location = location
        self.orderID = orderID 
        self.hauler = hauler 
        self.haulerQuote = haulerQuote 
        self.customerPrice = customerPrice
        self.sent_status = sent_status
        self.filename = filename


class Approvals(db.Model):
    __tablename__='approvals'
    id = db.Column(db.Integer,primary_key=True) 
    orderID = db.Column(db.String(10))