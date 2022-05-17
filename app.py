from flask import abort,Flask,g,session
from flask import render_template,request,redirect,flash,url_for,jsonify
from flask_wtf import FlaskForm
from wtforms import csrf
from wtforms import StringField,IntegerField
from wtforms.validators import InputRequired,Email
from wtforms import FileField
from flask_wtf.file import FileField,FileAllowed,FileRequired
from flask_uploads import configure_uploads,IMAGES,UploadSet
import random
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from functools import wraps
from twilio.request_validator import RequestValidator
import re
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy

basedir = Path(__file__).resolve().parent

'''deploy workflow
1. Commit changes locally...git add, git commit
2. Push changes to remote...go to push
3. In PA Pull down from remote....git pull
'''


app = Flask(__name__)

app.config['SECRET_KEY'] = "secret"
app.config['UPLOADED_IMAGES_DEST'] = 'static/images'

#max size of upload restricted
app.config['MAX_CONTENT_LENGTH'] = 8*1024*1024
app.config['UPLOADED_PHOTOS_ALLOW'] = ('png', 'jpg', 'jpeg','gif')

#for admin dash
USERNAME = "admin"
PASSWORD = "94YliJ$XhPui"

#'SHOW databases, USE flasksurfiary$marinhaulers'
SQLALCHEMY_DATABASE_URI = 'mysql://flasksurfdiary:testcred@flasksurfdiary.mysql.pythonanywhere-services.com/flasksurfdiary$marinhaulers'


SQLALCHEMY_TRACk_MODIFICATIONS = False


#need to add a config object
app.config.from_object(__name__)
db = SQLAlchemy(app)

#models has to come afte db installation
from models import Post


#project needs to be removed in PAW

account_sid = 'AC21008da45eda60eca4b12c0dc32f77c5'
auth_token='testcred'


images = UploadSet('images',IMAGES)
configure_uploads(app,images)

#creates orderform and links objects to names in html form
class OrderForm(FlaskForm):
    fname = StringField('fname',validators=[InputRequired()])
    email = StringField('email',validators=[InputRequired(),Email()])
    phone = StringField('phone',validators=[InputRequired()])
    #FileFiled obj comes from Flask-WTF
    #added server side validation that image is required, only images
    image = FileField('image',validators=[FileRequired(),FileAllowed(images,'Images only!')])
    slot = IntegerField('timeslot')
    location = IntegerField('location',validators=[InputRequired()])
    orderID = IntegerField('order')
    hauler = StringField('hauler')
    haulerQuote = StringField('haulerQuote')
    customerPrice = StringField('customerPrice')


@app.route('/',methods=['GET','POST'])
def index():
    form = OrderForm()

    #need to add a message for 413 error too large file
    if request.method == 'POST' and form.validate_on_submit():

        slot = request.form.getlist('mycheckbox')
        orderID = random.randint(0,1000)
        email = form.email.data
        fname = form.fname.data
        location = request.form.getlist('location')
        phone = form.phone.data
        #form.image is a FileField object
        uploaded_file = images.save(form.image.data)
        hauler="Unknown"
        haulerQuote="Unknown"
        customerPrice="Unknown"
        sent_status = "False"

        #write to database
        order = Post(time=slot[0],orderID=orderID,email=email,fname=fname,location=location[0],phone=phone,hauler=hauler,haulerQuote=haulerQuote,sent_status=sent_status,customerPrice=customerPrice,filename=uploaded_file)

        db.session.add(order)
        db.session.commit()

        sendApprovalTextRequest(location=location,slot=slot,orderID=orderID,filename=uploaded_file)

        return render_template('confirm.html',filename=uploaded_file,slot=slot,orderID=orderID)



    flash(form.image.errors)
    return render_template('trashmain.html',form=form)

    #pass it to templte

@app.route('/story', methods=['GET'])
def story():
    return render_template('story.html')



client = Client(account_sid,auth_token)


def sendApprovalTextRequest(filename,location,slot,orderID):

    locations = {"1":"Fairfax","2":"San Anselmo","3":"Mill Valley","4":"Novato","5":"San Rafael","6":"West Marin"}
    slots ={"1":"8am-12pm","2":"12pm-4pm"}

    body = 'Do you approve this job order ID'+str(orderID)+ 'in'+locations[location[0]]+' this Saturday around '+ slots[slot[0]]+'?'

    client.messages.create(
        body=body,
        from_='+17402004872',
        media_url=['http://www.marinhaulers.com'+url_for('static',filename='images/'+filename)],
        to='+13055884051'
            )
    return filename, location, slot

holding_tank = ['+13055884051','+17072924215','+14158271028','+14156991091','+14155324569','+14155788894','+14157454042','+4156507687' \
,'+14157417415','+19167707619','+15104700723','+15109388283','+17073931401','+17078576193','+17075866640','+14152508743','+14155723670','+17378885865','+14153204987','+15105020299','+14154839119','+14155783028']

numbers_to_message =['+13055884051']

def sendHaulersText(filename,location,slot):

    locations = {"1":"Fairfax","2":"San Anselmo","3":"Mill Valley","4":"Novato","5":"San Rafael","6":"West Marin"}
    slots ={"1":"8am-12pm","2":"12pm-4pm"}

    body = 'How much would you charge for this job in '+locations[location[0]]+' this Saturday around '+ slots[slot[0]]+'?'

    for number in numbers_to_message:
        client.messages.create(
            body=body,
            from_='+17402004872',
            media_url=['http://www.marinhaulers.com'+url_for('static',filename='images/'+filename)],
            to= number
                )

#webhook added to Twilio for replies to SMS

@app.route("/search",methods=['GET'])
def search():
    query = request.args.get("query")
    entries = db.session.query(models.Post)
    if query:
        return render_template('search.html',entries=entries,query=query)
    return render_template('search.html')



def validate_twilio_request(f):
    """validates that incoming messages came from twilio"""
    @wraps(f)
    def decorated_function(*args,**kwargs):
        #create instance of request validator class
        validator = RequestValidator(auth_token)

        request_valid = validator.validate(request.url,request.form,request.headers.get('X-TWILIO-SIGNATURE', ''))

        if request_valid:
            return f(*args,**kwargs)
        else:
            return abort(403)
    return decorated_function


@app.route("/sms", methods=['GET', 'POST'])
@validate_twilio_request
def incoming_sms():
    '''instead of dynamic reply - this should set status for a post to approved'''

    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    import re
    #check if the text body contains 'approved'
    match = re.search(r'(?i)approved',body).group()

    if match:
        #grab orderID from text body
        orderID = [int(s) for s in body.split() if s.isdigit()]

        #write approved status to DB
        db.session.query(Post).filter(Post.orderID==orderID).update({Post.sent_status: 'Approved'},synchronize_session=False)

        db.session.commit()

        #query DB for approved order
        order2text = db.session.query(Post).filter(Post.orderID==orderID).first()

        filename = order2text.filename
        location = order2text.location
        time = order2text.time

        #send haulers a quote request
        sendHaulersText(filename,location,time)

        approved = "True"

    return approved

@app.errorhandler(413)
def error413(e):
    return render_template('error413.html'), 413


@app.route("/admin",methods=["GET","POST"])
def admin():
    """searches, then displays database of trash runs"""
    entries = db.session.query(Post)
    return render_template('admin.html',entries=entries)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login/authentication/session management."""
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('admin'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """User logout/authentication/session management."""
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))


@app.route('/addPrice', methods=['POST'])
def add_entry():
    """add hauler quote from twilio text and add customer price to be billed in Xero"""
    if not session.get('logged_in'):
        abort(401)
    new_entry = models.Post(request.form['hauler'],request.form['haulerQuote'],request.form['customerPrice'])
    db.session.add(new_entry)
    db.session.commit()
    flash('New entry was posted')
    return redirect(url_for('index'))

@app.route('/delete/<post_id>',methods=['GET'])
def delete_entry(post_id):
    """delete post from database"""
    result = {'status':0,'message':'Error'}
    try:
        db.session.query(models.Post).filter_by(id=post_id).delete()
        db.session.commit()
        result = {'status':1,'message':'Post Deleted'}
        flash('The entry was deleted')
    except Exception as e:
        result = {'status':0,'message':repr(e)}
    return jsonify(result)





if __name__ == "__main__":
    app.run()