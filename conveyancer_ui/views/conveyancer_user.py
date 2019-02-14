import json
import requests

from . import utils
from datetime import datetime
from flask import (Blueprint, current_app, redirect, render_template, request, session, url_for)
from babel import numbers
from conveyancer_ui.views.auth import yoti_login_required


# This is the blueprint object that gets registered into the app in blueprints.py.
user = Blueprint('conveyancer_user', __name__)


@user.route("/registration-complete")
@yoti_login_required
def registration_complete():
    return render_template('app/user/registration_complete.html')


@user.route("/accept-agreement")
@yoti_login_required
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
        purchase_price = numbers.format_currency(
            agreement['purchase_price'],
            agreement['purchase_price_currency_code']
        )

        # Case reference is required in entire journey, so if not found redirect to index page
        if session.get('case_reference'):
            case_reference = session['case_reference']
        else:
            return redirect(url_for('index.index_page'))

        # get buyer lender name
        buyer_lender = "Gringott's Bank"

        is_selling = is_selling_property(case_reference)

        return render_template('app/user/accept_agreement.html', address=title['title']['address'],
                               purchase_price=purchase_price, is_selling=is_selling, buyer_lender=buyer_lender)
    else:
        return "Title agreement not found"


@user.route("/agreement-signing", methods=['GET', 'POST'])
@yoti_login_required
def agreement_signing():
    if request.method == 'GET':
        # Check if case is to buy or sell
        is_selling = is_selling_property(session['case_reference'])

        return render_template('app/user/agreement_signing.html', is_selling=is_selling,
                               error_message=request.args.get('error_message'))
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
        except Exception as e:
            return e
    else:
        return 405


@user.route("/agreement-signed")
@yoti_login_required
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


@user.route("/transfer-complete")
@yoti_login_required
def transfer_complete():
    # The user will be redirected from a link in an SMS message so read values from url to be available in session
    session['title_id'] = request.args.get('title_id')

    if session['title_id']:
        is_selling = None
        case_reference = None

        try:
            # Fetch case details
            case_res = requests.get(current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases',
                                    params={'title_number': str(session['title_id'])},
                                    headers={'Accept': 'application/json'})
            case = case_res.json()[0]
            case_reference = case['case_reference']
            session['case_reference'] = case_reference
            # check if case is to sell or buy
            is_selling = case['case_type'] == 'sell'
        except requests.exceptions.RequestException:
            raise requests.exceptions.RequestException("Case management API is down.")
        except Exception as e:
            return "Title number not found in any cases."

        if not is_selling:
            try:
                title_id = str(session['title_id'])
                # Call to fetch title address
                title_res = requests.get(current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_id,
                                         headers={'Accept': 'application/json'})
            except requests.exceptions.RequestException:
                raise requests.exceptions.RequestException("Conveyancer API is down.")

            title = title_res.json()
            address = title['title']['address']
        else:
            address = case['address']
        return render_template('app/user/transfer_complete.html', is_selling=is_selling, address=address)
    else:
        return redirect(url_for('index.index_page'))


@user.route("/agreement-context")
@yoti_login_required
def agreement_info():
    # The user will be redirected from a link in an SMS message so read values from url to be available in session
    session['title_id'] = request.args.get('title_id')

    if session['title_id']:
        try:
            # Fetch case details
            case_res = requests.get(current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases',
                                    params={'title_number': str(session['title_id'])},
                                    headers={'Accept': 'application/json'})
            case = case_res.json()[0]
            session['case_reference'] = case['case_reference']
            # check if case is to sell or buy
            is_selling = case['case_type'] == 'sell'
            return render_template('app/user/agreement_context.html', is_selling=is_selling)
        except requests.exceptions.RequestException:
            raise requests.exceptions.RequestException("Case management API is down.")
        except Exception as e:
            return "Title number not found in any cases."
    else:
        return redirect(url_for('index.index_page'))


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
        raise requests.exceptions.RequestException(
            'Case Management API return error code: ' + str(case_res.status_code)
        )
