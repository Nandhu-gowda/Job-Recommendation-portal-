#pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.3.1/en_core_web_sm-2.3.1.tar.gz

from flask import Flask, render_template, url_for, request, session, redirect
from pyresparser import ResumeParser
import nltk
nltk.download('stopwords')
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import sqlite3
import os
import base64
import secrets
from flask_session import Session

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

cursor.execute("create table if not exists user(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, phone TEXT, password TEXT, filename TEXT)")

cursor.execute("""create table if not exists profile(id INTEGER PRIMARY KEY AUTOINCREMENT,
                fname TXET,
                lname TEXT,
                email TEXT,
                phone TEXT,
                gender TEXT,
                dob TEXT,
                qualification TEXT,
                university TEXT,
                result TEXT,
                year TEXT,
                experiance TEXT,
                skills TEXT,
                languages TEXT,
                resume TEXT)""")

cursor.execute("create table if not exists company(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, phone TEXT, password TEXT)")

cursor.execute("""create table if not exists jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,
                job TXET,
                location TEXT,
                skills TEXT,
                date TEXT,
                description TEXT,
                cname TEXT,
                cemail TEXT)""")

cursor.execute("""create table if not exists applied(id TEXT,
                job TEXT,
                location TEXT,
                skills TEXT,
                date TEXT,
                description TEXT,
                cname TEXT,
                cemail TEXT,
                uemail TEXT,
                status TEXT)""")

cursor.execute("""create table if not exists certificates(id TEXT,
                email TEXT,
                certificate TEXT)""")


def JobRecommend():
    data = ResumeParser('resume.pdf').get_extracted_data()
    resumes = []
    resumes.append(f"Name: {data['name']}")
    resumes.append(f"Email: {data['email']}")
    resumes.append(f"Mobile Number: {data['mobile_number']}")
    resumes.append(f"Skills: {data['skills']}")
    resumes.append(f"College Name: {data['college_name']}")
    resumes.append(f"Degree: {data['degree']}")
    resumes.append(f"Company Names: {data['company_names']}")
    resumes.append(f"No Of Pages: {data['no_of_pages']}")
    resumes.append(f"Total Experience: {data['total_experience']}")

    
    import pickle

    # Load the trained classifier
    clf = pickle.load(open('clf.pkl', 'rb'))
    tfidf = pickle.load(open('tfidf.pkl', 'rb'))

    import re
    def cleanResume(txt):
        cleanText = re.sub('http\S+\s', ' ', txt)
        cleanText = re.sub('RT|cc', ' ', cleanText)
        cleanText = re.sub('#\S+\s', ' ', cleanText)
        cleanText = re.sub('@\S+', '  ', cleanText)  
        cleanText = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', cleanText)
        cleanText = re.sub(r'[^\x00-\x7f]', ' ', cleanText) 
        cleanText = re.sub('\s+', ' ', cleanText)
        return cleanText

    # Clean the input resume
    cleaned_resume = cleanResume(str(resumes))

    # Transform the cleaned resume using the trained TfidfVectorizer
    input_features = tfidf.transform([cleaned_resume])

    # Make the prediction using the loaded classifier
    prediction_id = clf.predict(input_features)[0]

    # Map category ID to category name
    category_mapping = {
        15: "Java Developer",
        23: "Testing",
        8: "DevOps Engineer",
        20: "Python Developer",
        24: "Web Designing",
        12: "HR",
        13: "Hadoop",
        3: "Blockchain",
        10: "ETL Developer",
        18: "Operations Manager",
        6: "Data Science",
        22: "Sales",
        16: "Mechanical Engineer",
        1: "Arts",
        7: "Database",
        11: "Electrical Engineering",
        14: "Health and fitness",
        19: "PMO",
        4: "Business Analyst",
        9: "DotNet Developer",
        2: "Automation Testing",
        17: "Network Security Engineer",
        21: "SAP Developer",
        5: "Civil Engineer",
        0: "Advocate",
    }

    category_name = category_mapping.get(prediction_id, "Unknown")

    print("Predicted Category:", category_name)
    return category_name

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()

    dp = session['profile']
    email = session['uemail']

    cursor.execute("select * from profile where email = '"+email+"'")
    result1 = cursor.fetchone()

    if result1:
        my_string = base64.b64encode(result1[-1]).decode('utf-8')
        f = open('resume.pdf', 'wb')
        f.write(result1[-1])
        f.close()
        query = "SELECT * FROM jobs"
        cursor.execute(query)
        results = cursor.fetchall()
        return render_template("userlog.html", dp = dp, my_string=my_string, results=results, job = JobRecommend())
    else:
        return render_template('userlog.html', dp = dp)

@app.route('/jobs')
def jobs():
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()

    email = session['uemail']
    dp = session['profile']

    query = "SELECT * FROM jobs"
    cursor.execute(query)
    results = cursor.fetchall()
    return render_template("jobs.html", dp = dp, results=results)

@app.route('/usignin', methods=['GET', 'POST'])
def usignin():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM user WHERE email = '"+email+"' AND password= '"+password+"'"
        cursor.execute(query)

        result = cursor.fetchone()  

        if result:
            session['profile']=result[-1]
            session['uemail']=email
         
            cursor.execute("select * from profile where email = '"+email+"'")
            result1 = cursor.fetchone()
  
            if result1:
                my_string = base64.b64encode(result1[-1]).decode('utf-8')
                f = open('resume.pdf', 'wb')
                f.write(result1[-1])
                f.close()
                query = "SELECT * FROM jobs"
                cursor.execute(query)
                results = cursor.fetchall()
                return render_template("userlog.html", dp = result[-1], my_string=my_string, results=results, job=JobRecommend())
            else:
                return render_template('userlog.html', dp = result[-1], email=email)
        else:
            return render_template('usignin.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')            

    return render_template('usignin.html')




@app.route('/usignup', methods=['GET', 'POST'])
def usignup():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        file = request.files['file']
        filename = file.filename
        print(filename)
        file_content = file.read()
        my_string = base64.b64encode(file_content).decode('utf-8')

        cursor.execute("insert into user values(NULL,?,?,?,?,?)", [name, email, phone, password, my_string])
        connection.commit()

        return render_template('usignin.html', msg='Successfully Registered')
    
    return render_template('usignup.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        data = request.form
        print(data)
        
        keys = []
        values = []
        for key in data:
            keys.append(key)
            values.append(data[key])
        
        print(keys)
        print(values)

        file = request.files['resume']

        values.append(file.read())

        cursor.execute("insert into profile values(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        connection.commit()

        dp = session['profile']
        email = session['uemail']

        cursor.execute("select * from profile where email = '"+email+"'")
        result1 = cursor.fetchone()
        print(result1)
        
        if result1:
            my_string = base64.b64encode(result1[-1]).decode('utf-8')
            f = open('resume.pdf', 'wb')
            f.write(result1[-1])
            f.close()

            cursor.execute("select * from certificates where email = '"+email+"'")
            result2 = cursor.fetchall()
            certificates = []
            if result2:
                for row in result2:
                    certificates.append(base64.b64encode(row[-1]).decode('utf-8'))
            
            return render_template("userlog.html", dp = dp, my_string=my_string, job=JobRecommend(), certificates=certificates)
        else:
            return render_template('userlog.html', dp = dp, email = email)
    return render_template('userlog.html')

@app.route('/profileupdate', methods=['GET', 'POST'])
def profileupdate():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        data = request.form
        print(data)
        
        keys = []
        values = []
        for key in data:
            keys.append(key)
            values.append(data[key])
        
        print(keys)
        print(values)

        file = request.files['resume']

        values.append(file.read())

        dp = session['profile']
        email = session['uemail']

        cursor.execute("delete from profile where email = '"+email+"'")
        connection.commit()

        cursor.execute("insert into profile values(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        connection.commit()

        cursor.execute("select * from profile where email = '"+email+"'")
        result1 = cursor.fetchone()
        print(result1)
        
        if result1:
            my_string = base64.b64encode(result1[-1]).decode('utf-8')
            f = open('resume.pdf', 'wb')
            f.write(result1[-1])
            f.close()

            cursor.execute("select * from certificates where email = '"+email+"'")
            result2 = cursor.fetchall()
            certificates = []
            if result2:
                for row in result2:
                    certificates.append(base64.b64encode(row[-1]).decode('utf-8'))
            
            return render_template("userlog.html", dp = dp, my_string=my_string, job=JobRecommend(), certificates=certificates)
        else:
            return render_template('userlog.html', dp = dp, email = email)
    return render_template('userlog.html')


@app.route('/viewprofile')
def viewprofile():
    dp = session['profile']
    email = session['uemail']

    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()

    cursor.execute("select * from profile where email = '"+email+"'")
    result = cursor.fetchone()
    print(result)
    if result:
        my_string = base64.b64encode(result[-1]).decode('utf-8')
        return render_template("profile.html", dp = dp, my_string=my_string, result=result)
    else:
        return render_template('userlog.html', dp = dp, email=email)

@app.route('/chome')
def chome():
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    query = "SELECT * FROM jobs WHERE cemail = '"+session['cemail']+"'"
    cursor.execute(query)
    results = cursor.fetchall()
    return render_template('companylog.html', results=results)

@app.route('/application')
def application():
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    query = "SELECT * FROM applied WHERE cemail = '"+session['cemail']+"'"
    cursor.execute(query)
    result = cursor.fetchall()
    print(result)
    return render_template('application.html', result=result)

@app.route('/Accept/<email>')
def Accept(email):
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    st = 'accepted'
    cursor.execute("update applied set status = '"+st+"' where uemail = '"+email+"'")
    connection.commit()
    return redirect(url_for('application'))

@app.route('/Reject/<email>')
def Reject(email):
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    st = 'rejected'
    cursor.execute("update applied set status = '"+st+"' where uemail = '"+email+"'")
    connection.commit()
    return redirect(url_for('application'))

@app.route('/csignin', methods=['GET', 'POST'])
def csignin():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM company WHERE email = '"+email+"' AND password= '"+password+"'"
        cursor.execute(query)

        result = cursor.fetchone()

        if result:
            session['cname'] = result[1]
            session['cemail'] = email
            query = "SELECT * FROM jobs WHERE cemail = '"+email+"'"
            cursor.execute(query)
            results = cursor.fetchall()
            return render_template('companylog.html', results=results)
        else:
            return render_template('csignin.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')            

    return render_template('csignin.html')


@app.route('/csignup', methods=['GET', 'POST'])
def csignup():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        cursor.execute("insert into company values(NULL,?,?,?,?)", [name, email, phone, password])
        connection.commit()

        return render_template('csignin.html', msg='Successfully Registered')
    
    return render_template('csignup.html')

@app.route('/addjob', methods=['GET', 'POST'])
def addjob():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        job = request.form['job']
        loc = request.form['loc']
        skill = request.form['skill']
        ldate = request.form['ldate']
        jd = request.form['jd']

        data = [job, loc, skill, ldate, jd, session['cname'], session['cemail']]
        print(data)

        cursor.execute("insert into jobs values(NULL,?,?,?,?,?,?,?)", data)
        connection.commit()

        query = "SELECT * FROM jobs WHERE cemail = '"+session['cemail']+"'"
        cursor.execute(query)
        results = cursor.fetchall()

        return render_template('companylog.html', msg='Successfully added', results=results)
    
    return render_template('csignup.html')

@app.route('/asignin', methods=['GET', 'POST'])
def asignin():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        email = request.form['email']
        password = request.form['password']

        if email == 'admin@gmail.com' and password == 'admin123':
            return render_template('adminlog.html')
        else:
            return render_template('asignin.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')            

    return render_template('asignin.html')

@app.route('/apply/<Id>')
def apply(Id):
    print(Id)
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    cursor.execute("select * from jobs where id = '"+str(Id)+"'")
    result = list(cursor.fetchone())
    print(result)

    dp = session['profile']
    email = session['uemail']
    
    result.append(email)
    result.append('pending')
    cursor.execute('insert into applied values(?,?,?,?,?,?,?,?,?,?)', result)
    connection.commit()
    return redirect(url_for('applied_jobs'))

@app.route('/applied_jobs')
def applied_jobs():
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()

    dp = session['profile']
    email = session['uemail']
        
    cursor.execute("select * from applied where uemail = '"+str(email)+"'")
    result = cursor.fetchall()
    print(result)
    return render_template("applied_jobs.html", dp = dp,result=result)

    
@app.route('/userlist')
def userlist():
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    cursor.execute("select * from profile")
    result = cursor.fetchall()
    print(result)
    return render_template('userlist.html', result=result)


@app.route('/companylist')
def companylist():
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    cursor.execute("select * from company")
    result = cursor.fetchall()
    print(result)
    return render_template('companylist.html', result=result)

@app.route('/jobslist')
def jobslist():
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    cursor.execute("select * from jobs")
    result = cursor.fetchall()
    print(result)
    return render_template('jobslist.html', result=result)


@app.route('/ahome')
def ahome():
    return render_template('adminlog.html')

@app.route('/Searchjob', methods=['GET', 'POST'])
def Searchjob():
    if request.method == 'POST':
        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        email = session['uemail']
        dp = session['profile']

        query = request.form['query'].lower()

        query = "SELECT * FROM jobs where LOWER(job) = '"+query+"' or LOWER(location) = '"+query+"'"
        cursor.execute(query)
        results = cursor.fetchall()
        return render_template("jobs.html", dp = dp, results=results)
    return render_template("jobs.html")

@app.route('/certificate', methods=['GET', 'POST'])
def certificate():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        email = session['uemail']
        dp = session['profile']

        file = request.files['file']
        data = file.read()

        cursor.execute("insert into certificates values(NULL,?,?)", [email, data])
        connection.commit()
        
        cursor.execute("select * from profile where email = '"+email+"'")
        result1 = cursor.fetchone()
        print(result1)
        
        if result1:
            my_string = base64.b64encode(result1[-1]).decode('utf-8')

            cursor.execute("select * from certificates where email = '"+email+"'")
            result2 = cursor.fetchall()
            certificates = []
            if result2:
                for row in result2:
                    certificates.append(base64.b64encode(row[-1]).decode('utf-8'))
            
            return render_template("userlog.html", dp = dp, my_string=my_string, job=JobRecommend(), certificates=certificates)
        else:
            return render_template('userlog.html', dp = dp, email = email)

    return render_template("certificates.html")


@app.route('/editjob/<Id>')
def editjob(Id):
    print(Id)
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    
    cursor.execute("select * from jobs where id = '"+str(Id+"'"))
    result = cursor.fetchone()
    print(result)
    return render_template('editjob.html', result=result)

@app.route('/deletejob/<Id>')
def deletejob(Id):
    print(Id)
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    
    cursor.execute("delete from jobs where id = '"+str(Id+"'"))
    connection.commit()

    query = "SELECT * FROM jobs WHERE cemail = '"+session['cemail']+"'"
    cursor.execute(query)
    results = cursor.fetchall()

    return render_template('companylog.html', msg='Successfully deleted', results=results)

@app.route('/updatejob', methods=['GET', 'POST'])
def updatejob():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        Id = str(request.form['id'])
        job = request.form['job']
        loc = request.form['loc']
        skill = request.form['skill']
        ldate = request.form['ldate']
        jd = request.form['jd']

        data = [job, loc, skill, ldate, jd, Id]
        print(data)

        cursor.execute("update jobs set job = ?, location = ?, skills = ?, date = ?,description = ? where id = ?", data)
        connection.commit()

        query = "SELECT * FROM jobs WHERE cemail = '"+session['cemail']+"'"
        cursor.execute(query)
        results = cursor.fetchall()

        return render_template('companylog.html', msg='Successfully Updated', results=results)
    
    return render_template('csignup.html')


@app.route('/deletejobs/<Id>')
def deletejobs(Id):
    print(Id)
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    
    cursor.execute("delete from jobs where id = '"+str(Id+"'"))
    connection.commit()

    return redirect(url_for('jobslist'))

@app.route('/deleteuser/<Id>')
def deleteuser(Id):
    print(Id)
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()

    cursor.execute("select * from profile where id = '"+str(Id+"'"))
    result = cursor.fetchone()

    cursor.execute("delete from user where email = '"+result[3]+"'")
    connection.commit()
    
    cursor.execute("delete from profile where id = '"+str(Id+"'"))
    connection.commit()

    return redirect(url_for('userlist'))

@app.route('/deletecompany/<Id>')
def deletecompany(Id):
    print(Id)
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    
    cursor.execute("delete from company where id = '"+str(Id+"'"))
    connection.commit()

    return redirect(url_for('companylist'))

@app.route('/logout')
def logout():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
