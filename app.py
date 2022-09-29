from flask import Flask, render_template, request
from ldap3 import Server, Connection
import os
from dotenv import load_dotenv
import datetime

app = Flask(__name__, static_url_path='/static')
app.config['DEBUG'] = False

# VARIABLES
load_dotenv()
app = Flask(__name__, static_url_path='/static')
app.secret_key = os.getenv('FLASK_KEY')
server = Server(os.getenv('SERVER'))
BASE_DN = os.getenv('BASE_DN')


def is_connected(ldap, username, password):
    conn = Connection(ldap, username, password)
    conn.start_tls()
    conn.bind()
    if not conn.last_error:
        message = None
        return True, message
    elif conn.last_error == 'invalidCredentials':
        message = 'invalidCredentials'
        print('{} : {}'.format(username, message))
        return False, message
    else:
        message = 'error'
        print(message)
        return False, message


def generate_sieve_script(first_name, last_name, message):
    first_last = '{}.{}'.format(first_name.lower(), last_name.lower())
    # CREATING script.sieve
    sieve = ('\n'+
             '# ******************************************************************************\n'+
             '# * Script file generated automatically by the \'Out Of Office extension\'.\n'+
             '# * Do not modify this part.\n'+
             '# *\n'+
             '# *	@redirection=false\n'+
             '# *	@addresses={} {}\n'.format(first_name.capitalize(), last_name.upper())+
             '# *	@redirection.address=\n'+
             '# *	@redirection.keepMessage=false\n'+
             '# *	@notification=true\n'+
             '# *	@notification.message={}\n'.format(message)+
             '# ******************************************************************************\n'+
             'require "vacation"; \n'+
             'keep;\n'+
             '\n'+
             'vacation :days 1 :subject "Out of office auto reply" text: \n'+
             '\n'+
             '{}\n'.format(message)+
             '\n'+
             '.\n'+
             ';\n'+
             '\n'+
             '# ******************************************************************************\n'+
             '# * End of script file generated automatically by the \'Out Of Office extension\'.\n'+
             '# * Do not modify this part.\n'+
             '# ******************************************************************************\n'+
             '\n'
             )
    # Writing sieve script
    path = 'sieve_scripts'
    file_name = '{}.sieve'.format(first_last)
    file = os.path.join(path, file_name)
    f = open(file, 'w')
    f.write(sieve)
    f.close()


def generate_csv(first_last, start_date, last_date):
    csv = '{},{},{}\n'.format(first_last, start_date, last_date)
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    path = 'csv/'
    file_name = 'list.csv'
    file = os.path.join(path, file_name)
    f = open(file, 'a')
    f.write(csv)
    f.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        x = datetime.datetime.now()
        min_date = x.strftime("%Y-%m-%d")
        return render_template('index.html', min_date=min_date)
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        ldap_username = 'CN={} {}{}'.format(first_name.capitalize(), last_name.upper(), BASE_DN)
        password = request.form['password']
        is_logged, error = is_connected(server, ldap_username, password)
        if is_logged:
            first_last = '{}.{}'.format(first_name.lower(), last_name.lower())
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            message = request.form['message']

            generate_sieve_script(first_name, last_name, message)
            generate_csv(first_last, start_date, end_date)

            return render_template('submit.html')
        else:
            return render_template('error.html', error=error)


if __name__ == "__main__":
    app.run()
