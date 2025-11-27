from flask import Flask, render_template, session
from bp_query.query_route import query_bp
from bp_auth.auth_route import auth_bp
from bp_report.report_route import report_bp
from basket.route import flight_bp
from access import login_required
import json


app = Flask(__name__, template_folder='template', static_folder='../static')
app.config['SECRET_KEY'] = '1234'


with open('../data/db_config.json') as f:
    app.config['db_config'] = json.load(f)

with open('../data/access.json') as f:
    app.config['access_config'] = json.load(f)

with open('../data/db_report.json') as f:
    app.config['reports_config'] = json.load(f)

with open('../data/cache_config.json') as f:
    app.config['cache_config'] = json.load(f)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(query_bp, url_prefix='/query')
app.register_blueprint(report_bp, url_prefix='/report')
app.register_blueprint(flight_bp, url_prefix='/basket')


@app.route('/')
@login_required
def main_menu():
    user_role = session.get('user_group', '')
    return render_template('main_menu.html', user_role=user_role)


@app.route('/exit')
@login_required
def exit_system():
    session.clear()
    return "👋 До свидания!"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)