import yagmail
from app import db
from models import Post
from sqlalchemy import create_engine,update,MetaData,Table,Column,Integer,String



engine = create_engine("mysql://flasksurfdiary:testcred@flasksurfdiary.mysql.pythonanywhere-services.com/flasksurfdiary$marinhaulers",echo = True)
conn = engine.connect()


def sendConfirm(email,fname,orderID,location,slot,phone):
    receiver = [email,'quote@marinhaulers.com']
    body = fname+ " ,your order ID is "+str(orderID)+ " If you don't receive a quote in 3 hours \
    email your order ID to quote@marinhaulers.com to follow up"
    #change back to '/home/flasksurfdiary/trashapp/static/images/'+filename for server

    #attachments = 'C:\\Users\\rskov\\Projects\\trashapp\\project\\static\\images\\'+filename
    #attachments = '/home/flasksurfdiary/trashapp/static/images/'+filename
    yag = yagmail.SMTP('quote@marinhaulers.com','testcred')

    yag.send(
        to=receiver,
        subject="Quote confirmation from marinhaulers.com",
        contents=body,
        #attachments = attachments
    )


#query db for unsent confirms
#dump unsent confirms in to a list in case there's multiple confirms

unsent_emails = db.session.query(Post).filter_by(sent_status='Approved')

#send confirm email

for unsent_email in unsent_emails:
   sendConfirm(unsent_email.email,unsent_email.fname,unsent_email.orderID,unsent_email.location,unsent_email.time,unsent_email.phone)

#mark sent in db

meta = MetaData()
orders = Table(
    'orders',
    meta,
    Column('id',Integer,primary_key=True),
    Column('sent_status',String),
)

stmt = orders.update().where(orders.c.sent_status=='Approved').values(sent_status='True')
conn.execute(stmt)

