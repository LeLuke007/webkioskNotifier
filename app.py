from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import requests, os
import smtplib

app = Flask(__name__)

headers = {
    "Connection": "keep-alive",
    "Origin": "https://webkiosk.thapar.edu",
    "Referer": "https://webkiosk.thapar.edu/"
}

logindata = {
    "txtuType": "Member Type",
    "UserType": "S",
    "txtCode": "Enrollment No",
    "MemberCode": os.environ.get('RollNumber'),
    "txtPin": "Password/Pin",
    "Password": os.environ.get('WebkioskPassword')
}

sem = os.environ.get('Sem')
emailID = os.environ.get('emailID')

loginurl = 'https://webkiosk.thapar.edu/CommonFiles/UserAction.jsp'
marksurl = f'https://webkiosk.thapar.edu/StudentFiles/Exam/StudentEventMarksView.jsp?x=&exam={sem}'

def get_marks():
    with requests.Session() as c:
        c.post(loginurl, logindata, headers=headers)
        page = c.get(marksurl)
        return int(page.text.count('<td nowrap>') - 1)  # count('<td nowrap>') - 4

def read_current():
    with open("currentVal.txt", "r") as f:
        return int(f.read())

def remove_lock_file():
    if os.path.exists("email_sent.lock"):
        os.remove("email_sent.lock")

def send_mail():
    try:
        current = read_current()
        tr = get_marks()
        if tr > current:
            if os.path.exists("email_sent.lock"):
                print("Email already sent in this interval.")
                return
            
            msg = """Subject: New Marks Uploaded """
            fromaddr = "knightdarkhero@gmail.com"
            password = "dvid btvn iqxn btag"
            
            if os.path.exists('maillist.txt'):
                with open("maillist.txt", "r") as f:
                    toaddrs = f.read().strip().split("\n")
            else:
                toaddrs = emailID

            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(fromaddr, password)
            server.sendmail(fromaddr, toaddrs, msg)

            with open("currentVal.txt", "w") as f:
                f.write(str(tr))
                
            open("email_sent.lock", "w").close()
            server.quit()
            print("Marks Uploaded", tr)
            
    except Exception as e:
        print("Error Occurred:", str(e))

scheduler = BackgroundScheduler()
scheduler.add_job(send_mail, 'interval', seconds=10)
scheduler.add_job(remove_lock_file, 'interval', seconds=10)
scheduler.start()

@app.route('/')
def index():
    return 'Flask App with Scheduler Running!'

if __name__ == '__main__':
    app.run(debug=True)
