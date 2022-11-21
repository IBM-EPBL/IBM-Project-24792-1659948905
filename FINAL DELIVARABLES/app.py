from turtle import st
from flask import Flask, render_template, request, redirect, url_for, session
from markupsafe import escape
import ibm_db
from newsapi import NewsApiClient

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=0c77d6f2-5da9-48a9-81f8-86b520b87518.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31198;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=htd44349;PWD=lHb7NTRWyaRrlgWz",'','')

newsapi = NewsApiClient(api_key='9ff3955d6a1e4752b1f35b45ed3c2f44')
global login
login = False
app=Flask(__name__)
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/index")
def index():
    return render_template("index.html")

# helper function
def get_sources_and_domains():
	all_sources = newsapi.get_sources()['sources']
	sources = []
	domains = []
	for e in all_sources:
		id = e['id']
		domain = e['url'].replace("http://", "")
		domain = domain.replace("https://", "")
		domain = domain.replace("www.", "")
		slash = domain.find('/')
		if slash != -1:
			domain = domain[:slash]
		sources.append(id)
		domains.append(domain)
	sources = ", ".join(sources)
	domains = ", ".join(domains)
	return sources, domains

@app.route('/addmember',methods = ['POST', 'GET'])
def addmember():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        con_password = request.form['con-password']
        sql = "SELECT * FROM NEWSTRACKER WHERE name =?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,name)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        if account:
            return render_template('inner-page.html', msg="You are already a member, please login using your details")
        else:
            insert_sql = "INSERT INTO NEWSTRACKER VALUES (?,?,?,?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, name)
            ibm_db.bind_param(prep_stmt, 2, email)
            ibm_db.bind_param(prep_stmt, 3, password)
            ibm_db.bind_param(prep_stmt, 4, con_password)
            ibm_db.execute(prep_stmt)
        return render_template('signin.html', request="successfully created")


@app.route('/checkmember',methods = ['POST', 'GET'])
def check_member():
    global login
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        sql = "SELECT * FROM NEWSTRACKER WHERE email = '" + email +"'"
        stmt = ibm_db.exec_immediate(conn, sql)
        account = ibm_db.fetch_both(stmt)
        if not account:
            return render_template('signin.html', msg = "enter valid email")
        if account['PASSWORD'] == password:
            login = True
            return redirect(url_for('main'))
        return render_template('signin.html',msg2="invalid password")

@app.route('/signup',methods = ['POST', 'GET'])
def signup():
    global login
    login = False
    return render_template('inner-page.html')

@app.route('/signin',methods = ['POST', 'GET'])
def signin():
    global login
    login = False
    return render_template('signin.html')

@app.route('/main',methods = ['POST','GET'])
def main():
    global login
    if login == False:
         return render_template('signin.html',msg3="Signin Required")
    if request.method == "POST":
        sources, domains = get_sources_and_domains()
        keyword = request.form["keyword"]
        related_news = newsapi.get_everything(q=keyword,
                                      sources=sources,
                                      domains=domains,
                                      language='en',
                                      sort_by='relevancy')
        no_of_articles = related_news['totalResults']
        if no_of_articles > 100:
            no_of_articles = 100
        all_articles = newsapi.get_everything(q=keyword,
                                      sources=sources,
                                      domains=domains,
                                      language='en',
                                      sort_by='relevancy',
                                      page_size = no_of_articles)['articles']
        return render_template("main.html", all_articles = all_articles, 
                               keyword=keyword)
    else:
        top_headlines = newsapi.get_top_headlines(country="in", language="en")
        total_results = top_headlines['totalResults']
        if total_results > 100:
            total_results = 100
        all_headlines = newsapi.get_top_headlines(country="in",
                                                     language="en", 
                                                     page_size=total_results)['articles']
        return render_template("main.html", all_headlines = all_headlines)
    return render_template("main.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
