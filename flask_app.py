import flask
import csv
import searchdata.quarterdates as QD
from flask_sqlalchemy import SQLAlchemy
from pytz import timezone


app = flask.Flask(__name__)
app.config["DEBUG"] = True

##initialize database
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="eharris",
    password="erinssql1",
    hostname="eharris.mysql.pythonanywhere-services.com",
    databasename="eharris$UCLARec",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Stamp(db.Model):

    __tablename__ = "UCLARec"

    id = db.Column(db.Integer, primary_key=True)
    quarter = db.Column(db.String(240))
    ucla_id = db.Column(db.Integer)
    firstname = db.Column(db.String(120))
    lastname = db.Column(db.String(120))
    date = db.Column(db.String(240))
    classname = db.Column(db.String(240))

def getday():
    date  = QD.datetime.now().astimezone(timezone('US/Pacific'))
    return  date ##debug: QD.datetime.strptime("2017-11-07", "%Y-%m-%d")

def getquarter():
    day = getday()
    for i in QD.quarters:
        if day >= i.begin and day <= i.end:
            return i.season + "" + i.year


##HOMEPAGE
@app.route("/")
def index():

    ##get date
    today = getday()

    ##get quarter
    quarter = getquarter()

    classes = []

    weekday = today.strftime('%a')

    ##select options of classes based on dates
    with open('/home/eharris/mysite/searchdata/' + quarter + '.csv', "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[0] == weekday:
                    classes = row[1:]

    ##create multideimentional list of classes and names such that [0] is the name of the class and the rest are the students
    names_list = []
    classes.sort()
    for i in classes:
        class_list = [i]

        ##get all students from class
        s = Stamp.query.filter_by(quarter=quarter,classname=i).order_by(Stamp.ucla_id)

        ##get first, last, and ids and format
        for k in s:
            ##format name so "id first last"
            name = str(k.ucla_id)+ ' ' + k.firstname + ' ' + k.lastname
            ##if the name is already on the list, no need to append it
            if name not in class_list:
                class_list.append(name)

        names_list.append(class_list)

    return flask.render_template("index.html", date=today.strftime('%B %d %Y'), quarter=quarter, class_list=classes,  names_list=names_list)


##STUDENTS SUBMIT
@app.route("/submit",  methods=['POST'])
def submit():
    ##all processing of data of student will happen here.
    ##get info from user submiting
    firstname = flask.request.form['firstname']
    lastname = flask.request.form['lastname']
    ucla_id  = flask.request.form['ID']
    classname = flask.request.form['class']
    fullinfo = flask.request.form['fullinfo']

    ##get quarter and day
    today = getday()
    quarter = getquarter()

    ##if a returning user
    if(fullinfo != "0"):
        info = fullinfo.split()
        ucla_id = int(info[0])
        firstname = info[1]
        lastname = info[2]

    s = Stamp(quarter = quarter,ucla_id = int(ucla_id), firstname = firstname, lastname = lastname, date = today.strftime('%Y-%m-%d'), classname = classname)
    db.session.add(s)
    db.session.commit()


    return flask.render_template("submit.html",classname = classname, name = firstname + " " + lastname)



##EVERYTHING ADMIN##

##LOGIN PAGE##
@app.route("/login", methods=['GET','POST'])
def login():
    error = None
    if flask.request.method == 'POST':
        user = flask.request.form['user']
        password = flask.request.form['password']
        if user == 'uclarec' and password == 'gobruins':
            return flask.redirect(flask.url_for('admin'))
        else:
             error = 'Invalid username or password. Please try again!'
    return flask.render_template("login.html", error=error)


##ADMIN DIRECTORY
@app.route("/admin")
def admin():
    return flask.render_template("admin.html")


##ADMIN ADD A CLASS
@app.route("/addclass")
def addclass():
    return flask.render_template("addclass.html", error = None)


##ADMIN SUBMIT ADD A CLASS
@app.route("/submitclass",methods=['POST'])
def submitclass():
    ##all processing of data from an added class will happen here

    ##get the info from the form
    classname = flask.request.form['classname']
    quarter = flask.request.form['quarter']
    days  = flask.request.form.getlist('days')

    ##write to search file with class data
    try:
        all = []
        with open('/home/eharris/mysite/searchdata/' + quarter + '.csv', "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if classname in row:
                    return flask.render_template("addclass.html", error="That class already exists!")
                if row[0] in days and classname not in row:
                    row.append(classname)
                all.append(row)

        with open('/home/eharris/mysite/searchdata/' + quarter + '.csv', 'w') as csvoutput:
                writer = csv.writer(csvoutput, lineterminator='\n')
                writer.writerows(all)
    except IOError:
        pass


    return flask.render_template("submitclass.html", classname=classname, days=days, quarter=quarter)


##ADMIN DELETE CLASS
@app.route("/deleteclass")
def deleteclass():
    ##get quarter
    quarter = getquarter()

    ##get classnames from quarter
    classes = []
    ##get classnames
    with open('/home/eharris/mysite/searchdata/' + quarter + '.csv', "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                for i in range(len(row)):
                    if i != 0 and row[i] not in classes:
                        classes.append(row[i])
    classes.sort()

    ##get student numbers and add to classname- format: name-n students
    class_nums = []
    for i in range(len(classes)):
        s = Stamp.query.filter_by(classname=classes[i])
        students = []
        for j in s:
            if j.ucla_id not in students:
                students.append(j.ucla_id)
        class_nums.append(classes[i]+'-' + str(len(students)))

    return flask.render_template("deleteclass.html", class_list=class_nums)

##ADMIN SUBMIT DELETE CLASS
@app.route("/submitdeleteclass", methods=['POST'])
def submitdeleteclass():
    ##get quarter
    quarter = getquarter()

    #get class info in format: name-x students
    classinfo = flask.request.form['class']

    #split classinfo at -
    classinfo = classinfo.split('-')

    #get class name
    classname = classinfo[0]

    ##delete any instances of the class in the database
    s = Stamp.query.filter_by(classname=classname)
    for i in s:
        db.session.delete(i)
    db.session.commit()

    ##delete any instances from searchdata csv
    try:
        all = []
        with open('/home/eharris/mysite/searchdata/' + quarter + '.csv', "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                new_row = []
                for w in row:
                    if w != classname:
                        new_row.append(w)
                all.append(new_row)

        with open('/home/eharris/mysite/searchdata/' + quarter + '.csv', 'w') as csvoutput:
                writer = csv.writer(csvoutput, lineterminator='\n')
                writer.writerows(all)
    except IOError:
        pass

    return flask.render_template("submitdeleteclass.html", classname = classname, quarter = quarter)

##ADMIN CHANGE ATTENDANCE
@app.route("/changeattendance")
def changeattendance():
    ##get quarter
    quarter = getquarter()

    #get classes available from quarter
    classes = []
    #get classnames
    with open('/home/eharris/mysite/searchdata/' + quarter + '.csv', "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                for i in range(len(row)):
                    if i != 0 and row[i] not in classes:
                        classes.append(row[i])
    classes.sort()

    #create a 2d array where each array has the class name and then the list of its students
    names_list = []
    for i in classes:
        class_list = [i]

        ##get all students from class
        s = Stamp.query.filter_by(quarter=quarter,classname=i).order_by(Stamp.ucla_id)

        ##get first, last, and ids and format
        for k in s:
            ##format name so "id first last"
            name = str(k.ucla_id)+ ' ' + k.firstname + ' ' + k.lastname
            ##if the name is already on the list, no need to append it
            if name not in class_list:
                class_list.append(name)

        names_list.append(class_list)

    #TODO: get list of dates for each student for delete function

    return flask.render_template("changeattendance.html", quarter=quarter, class_list=classes, names_list=names_list)

##ADMIN COMING SOON
@app.route("/comingsoon")
def comingsoon():
    return flask.render_template("comingsoon.html", error = None)

if __name__ == '__main__':
    app.run()