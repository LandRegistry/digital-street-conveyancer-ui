from flask import Blueprint, render_template, url_for, request, redirect, current_app, session, Markup
import requests
from datetime import datetime
from babel import numbers
from . import utils
from conveyancer_ui.views.login import login_required
from conveyancer_ui.views.login import logout
import json


# This is the blueprint object that gets registered into the app in blueprints.py.
user = Blueprint('conveyancer_user', __name__)


@user.route("/accept-agreement")
def accept_agreement():
    try:
        title_id = str(session['title_id'])
        # Call to fetch title address
        title_res = requests.get(current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_id,
                                 headers={'Accept': 'application/json'})
        # Fetch agreement details
        url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_id + '/sales-agreement'
        agreement_res = requests.get(url, headers={'Accept': 'application/json'})
    except requests.exceptions.RequestException:
        raise requests.exceptions.RequestException("Conveyancer API is down.")

    if title_res.status_code == 200:
        title = title_res.json()
        agreement = agreement_res.json()

        # Convert purchase price from float to currency format
        purchase_price = numbers.format_currency(agreement['purchase_price'], agreement['purchase_price_currency_code'])

        buyer_lender = "Gringott Bank"
        # Case reference is required in entire journey, so if not found redirect to index page
        if session.get('case_reference'):
            case_reference = session['case_reference']
        else:
            return redirect(url_for('index.index_page'))
        is_selling = is_selling_property(case_reference)

        return render_template('app/user/accept_agreement.html', address=title['title']['address'],
                               purchase_price=purchase_price, is_selling=is_selling, buyer_lender=buyer_lender)
    else:
        return "Title agreement not found"


@user.route("/agreement-signing", methods=['GET', 'POST'])
def agreement_signing():
    if request.method == 'GET':
        # Check if case is to buy or sell
        is_selling = is_selling_property(session['case_reference'])

        return render_template('app/user/agreement_signing.html', is_selling=is_selling)
    elif request.method == 'POST':
        # Invoke the BuyerSignAgreement flow when the form is submitted
        try:
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

            # api to get signatory
            url = current_app.config['CONVEYANCER_API_URL'] + '/me'
            signatory_res = requests.get(url, headers={'Accept': 'application/json'})
            signatory = signatory_res.json()
            agreement_approval_data = {"action": "sign",
                                       "signatory": signatory['me'],
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
        except Exception as e:
            return e
    else:
        return 405


@user.route("/agreement-signed")
def agreement_signed():
    try:
        title_id = str(session['title_id'])
        # Call to fetch title address
        title_res = requests.get(current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_id,
                                 headers={'Accept': 'application/json'})

        # Fetch agreement details
        url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_id + '/sales-agreement'
        agreement_res = requests.get(url, headers={'Accept': 'application/json'})
    except requests.exceptions.RequestException:
        raise requests.exceptions.RequestException("CONVEYANCER API is down.")

    title = title_res.json()
    agreement = agreement_res.json()

    # Change date format
    completion_date = utils.custom_strftime('{S} %B %Y', datetime.strptime(agreement['completion_date'],
                                            "%Y-%m-%dT%H:%M:%S"))

    # Check if case is to buy or sell
    is_selling = is_selling_property(session['case_reference'])

    return render_template('app/user/agreement_signed.html', address=title['title']['address'],
                           completion_date=completion_date, is_selling=is_selling)


@user.route("/complete-notify")
def complete_notify():
    # In the previous step user would have logged out so read values from url to be available in session
    session['title_id'] = request.args.get('title_id')
    # Fetch case reference from title id
    case_res = requests.get(current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases',
                            params={"title_number": session['title_id']}, headers={'Accept': 'application/json'})
    if case_res.status_code == 200:
        cases = case_res.json()

        # Save to session
        for case in cases:
            session['case_reference'] = case['case_reference']
    return render_template('app/user/complete_notify.html')


@user.route("/transfer-complete")
@login_required
def transfer_complete():
    # Case reference is required in entire journey, so if not found redirect to index page
    if session.get('case_reference'):
        case_reference = session['case_reference']
    else:
        return redirect(url_for('index.index_page'))
    is_selling = is_selling_property(case_reference)

    # after the transfer the seller conveyancer object does not have title details so fetch from case management
    if not is_selling:
        try:
            title_id = str(session['title_id'])
            # Call to fetch title address
            title_res = requests.get(current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_id,
                                     headers={'Accept': 'application/json'})
        except requests.exceptions.RequestException:
            raise requests.exceptions.RequestException("Conveyancer API is down.")

        # Response
        title = title_res.json()
        address = title['title']['address']
    else:
        try:
            # Call to fetch title address
            case_res = requests.get(current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases/' + case_reference,
                                     headers={'Accept': 'application/json'})
        except requests.exceptions.RequestException:
            raise requests.exceptions.RequestException("Case management API is down.")

            # Response
        title = case_res.json()
        address = title['address']
    return render_template('app/user/transfer_complete.html', is_selling=is_selling, address=address)


@user.route("/agreement-transfer-notify")
def agreement_transfer_notify():
    # log users out when on this screen to start next seller/buyer flow
    logout()

    # save title id back in session after log out
    session['title_id'] = request.args.get('title_id')
    # Fetch case reference from title id
    case_res = requests.get(current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases',
                            params={"title_number": session['title_id']}, headers={'Accept': 'application/json'})
    if case_res.status_code == 200:
        cases = case_res.json()

        # Save to session
        for case in cases:
            session['case_reference'] = case['case_reference']
            # check if case is to sell or buy
            is_selling = is_selling_property(case['case_reference'])

    return render_template('app/user/agreement_transfer_notify.html', is_selling=is_selling)


@user.route("/agreement-context")
@login_required
def agreement_info():
    # In the previous step user would have logged out so read values from url to be available in session
    session['case_reference'] = request.args.get('case_reference')
    session['title_id'] = request.args.get('title_id')

    # check if case is to sell or buy
    is_selling = is_selling_property(session['case_reference'])
    return render_template('app/user/agreement_context.html', is_selling=is_selling)


@user.route("/countdown")
def countdown():
    try:
        # Fetch agreement details
        title_id = str(session['title_id'])
        url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_id + '/sales-agreement'
        agreement_res = requests.get(url, headers={'Accept': 'application/json'})
    except requests.exceptions.RequestException:
        raise requests.exceptions.RequestException("Conveyancer API is down.")
    agreement = agreement_res.json()

    # Get date object to change to string
    completion_date = datetime.strptime(agreement['completion_date'], "%Y-%m-%dT%H:%M:%S")
    query_str = Markup('/user/complete-notify?title_id=' + title_id + '&case_reference=' + session['case_reference'])
    return render_template('app/user/countdown.html',
                           completionDate=completion_date.strftime("%Y-%m-%dT%H:%M:%S"),
                           serverNowDate=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                           counterparty_conveyancer_ui_url=current_app.config['COUNTER_CONVEYANCER_UI_URL'],
                           notification_url_path=query_str)


# Function to check if a case is to buy or sell
def is_selling_property(case_reference):
    try:
        # Fetch case details
        case_res = requests.get(current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases/' + case_reference,
                                headers={'Accept': 'application/json'})
    except requests.exceptions.RequestException:
        raise requests.exceptions.RequestException('Case Management API is down.')

    if case_res.status_code == 200:
        case = case_res.json()

        # check if case is to sell or buy
        if case['case_type'] == "sell":
            return True
        else:
            return False
    else:
        raise requests.exceptions.RequestException('Case Management API return error code: ' + str(case_res.status_code))
