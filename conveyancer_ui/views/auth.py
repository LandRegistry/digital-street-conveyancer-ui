from flask import Blueprint, render_template, url_for, request, redirect, current_app, session
from functools import wraps
import json
import requests
from yoti_python_sdk import Client

# This is the blueprint object that gets registered into the app in blueprints.py.
auth = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('auth.login', next=request.full_path))
    return decorated_function


def yoti_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' in session:
            return f(*args, **kwargs)
        else:
            if current_app.config.get('YOTI_AUTH') == "TRUE":
                return redirect(url_for('auth.login_yoti', next=request.full_path))
            else:
                return redirect(url_for('auth.login', next=request.full_path))
    return decorated_function


@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_details_res = requests.get(
            current_app.config['CASE_MANAGEMENT_API_URL'] + '/users', params={
                "email_address": str(request.form.get('email').lower())
            },
            headers={'Accept': 'application/json'})
        user_details = json.loads(user_details_res.text)
        if user_details:
            for user in user_details:
                session['user_name'] = user['first_name'] + " " + user['last_name']
                session['user_id'] = user['identity']
                session['email'] = user['email_address']
            return redirect(request.form.get('redirect_url'))
        else:
            # in case of invalid credentials, the previous redirect url is
            # lost so pass it back to the login form in a new variable
            redirect_url = request.form.get('redirect_url')
            return render_template('app/login.html', redirect_url=redirect_url, error_message="User not found.")

    if request.method == 'GET':
        if 'user_name' in session:
            return redirect(url_for('conveyancer_admin.case_list'))
        redirect_url = ""
        # handle any malicious redirects in the login URL
        if request.args.get('next', ''):
            # append the next url to the domain name
            redirect_url = request.url_root.strip("/") + request.args.get('next', '')
        return render_template('app/login.html', redirect_url=redirect_url)


@auth.route("/logout/")
@login_required
def logout():
    session.clear()
    # gc.collect()
    return redirect(url_for('index.index_page'))


@auth.route("/yoti-login")
def login_yoti():
    return render_template('app/yoti_login.html', next=request.args.get('next'))


@auth.route("/login-callback")
def login_callback():
    client = Client(current_app.config['YOTI_CLIENT_SDK_ID'], current_app.config['YOTI_KEY_FILE_PATH'])
    token = request.args.get('token')
    if token:
        activity_details = client.get_activity_details(token)
        user_profile = activity_details.user_profile
        email_address = user_profile.get('email_address')
        user_details_res = requests.get(
            current_app.config['CASE_MANAGEMENT_API_URL'] + '/users', params={
                "email_address": email_address.lower()
            },
            headers={'Accept': 'application/json'})
        user_details = json.loads(user_details_res.text)
        if user_details:
            for user in user_details:
                session['user_name'] = user['first_name'] + " " + user['last_name']
                session['user_id'] = user['identity']
                session['email'] = user['email_address']
                return redirect(request.args.get('next'))
        else:
            redirect_url = request.args.get('next')
            return render_template('app/yoti_login.html', next=redirect_url, error_message="User not found")
    else:
        # in case of missing Yoti token, the previous redirect url is
        # lost so pass it back to the login form in a new variable
        redirect_url = request.args.get('next')
        return render_template('app/yoti_login.html', next=redirect_url, error_message="Token not found.")


@auth.route("/register")
def register_yoti():
    error_message = request.args.get('error_message')
    return render_template('app/yoti_register.html', error_message=error_message)


@auth.route("/register-callback")
def register_callback():
    client = Client(current_app.config['YOTI_CLIENT_SDK_ID'], current_app.config['YOTI_KEY_FILE_PATH'])
    token = request.args.get('token')
    if token:
        try:
            activity_details = client.get_activity_details(token)
            user_profile = activity_details.user_profile

            user_request = {
                'identity': activity_details.user_id,
                # if given_names or family_name are missing, get the first/last name in full_name respectively
                'first_name': user_profile.get('given_names', user_profile.get('full_name').split()[0]),
                'last_name': user_profile.get('family_name', user_profile.get('full_name').split()[-1]),
                'email_address': user_profile.get('email_address'),
                'phone_number': user_profile.get('phone_number'),
                'address': {
                    'house_name_number': '',
                    'street': '',
                    'town_city': '',
                    'county': '',
                    'country': '',
                    'postcode': 'BS2 8EN'
                }
            }
            user_details_res = requests.post(
                current_app.config['CASE_MANAGEMENT_API_URL'] + '/users',
                data=json.dumps(user_request),
                headers={'Accept': 'application/json',
                         'Content-Type': 'application/json'})
            user_details = user_details_res.json()
            if user_details:
                session['user_name'] = user_details['first_name'] + " " + user_details['last_name']
                session['user_id'] = user_details['identity']
                session['email'] = user_details['email_address']
                return redirect(url_for('conveyancer_user.registration_complete'))
            else:
                return redirect(url_for('auth.register_yoti', error_message="User not found"))
        except Exception as e:
            return redirect(url_for('auth.register_yoti', error_message=str(e)))
    else:
        # in case of missing Yoti token, the previous redirect url is
        # lost so pass it back to the login form in a new variable
        return render_template('app/register_yoti.html', error_message="Token not found.")


@auth.route("/sign-callback")
def sign_callback():
    yoti_client = Client(current_app.config['YOTI_CLIENT_SDK_ID'], current_app.config['YOTI_KEY_FILE_PATH'])
    token = request.args.get('token')
    if token:
        try:
            activity_details = yoti_client.get_activity_details(token)

            title_number = str(session['title_id'])

            # API to fetch seller's details
            url = current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases'
            case_details_res = requests.get(url, params={"title_number": title_number, "embed": "client"},
                                            headers={'Accept': 'application/json'})

            # Response
            case_details_obj = case_details_res.json()
            client = {}
            for case in case_details_obj:
                client = case['client']
            client['type'] = "individual"

            # Check that the current user is authorised to sign the agreement
            if client['identity'] == activity_details.user_id:

                url = current_app.config['CONVEYANCER_API_URL'] + '/me'
                signatory_res = requests.get(url, headers={'Accept': 'application/json'})
                signatory = signatory_res.json()
                agreement_approval_data = {
                    "action": "sign",
                    "signatory": signatory['me']['x500'],
                    "signatory_individual": client
                }

                # Sign contract
                url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_number + "/sales-agreement"
                response = requests.put(url, data=json.dumps(agreement_approval_data),
                                        headers={'Accept': 'Application/JSON', 'Content-Type': 'Application/JSON'})

                # Output
                if response.status_code == 200:
                    return redirect(url_for('conveyancer_user.agreement_signed'))
                else:
                    return "Something went wrong:<br>" + response.text.replace("\n", "<br/>")

            else:
                error_message = "User not authorised to sign"
                redirect_url = request.args.get('next')
                return redirect(url_for('conveyancer_user.agreement_signing', redirect_url=redirect_url,
                                        error_message=error_message))

        except Exception as e:
            error_message = str(e)
            redirect_url = request.args.get('next')
            return redirect(url_for('conveyancer_user.agreement_signing', redirect_url=redirect_url,
                                    error_message=error_message))
    else:
        return 'Yoti token missing'
