import json
import os.path
import requests

from babel import numbers
from conveyancer_ui.views.auth import login_required
from datetime import datetime
from flask import (Blueprint, current_app, redirect, render_template, request,
                   session, url_for)


# This is the blueprint object that gets registered into the app in blueprints.py.
admin = Blueprint('conveyancer_admin', __name__)

extras_filepath = 'extras.json'

request_data = {
    "titleId": '',
    "confirmIdentity": True
}


@admin.route("/case-list")
@login_required
def case_list():
    # Initialise all dictionaries
    status_dict = {}
    cases = {}

    # fetch all cases
    try:
        # Fetch all cases of the conveyancer
        cases = requests.get(current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases',
                             params={"embed": "client"},
                             headers={'Accept': 'application/json'})

    except requests.exceptions.RequestException as e:
        return render_template('app/admin/case_list.html', error_message=str(e), cases={}, status_dict={},
                               admin_notify="", admin=True)

    case_res = cases.json()

    # Fetch status values from conveyancer api
    try:
        cases = {
            'selling': list(case for case in filter(lambda x: x['case_type'].lower() == 'sell', case_res)),
            'buying': list(case for case in filter(lambda x: x['case_type'].lower() == 'buy', case_res))
        }
    except KeyError:
        return "Case type missing in API response"

    try:
        # Call to fetch the status of cases of the conveyancer
        title_status_res = requests.get(current_app.config['CONVEYANCER_API_URL'] + '/titles',
                                        headers={'Accept': 'application/json'})

    except requests.exceptions.RequestException as e:
        return render_template('app/admin/case_list.html', error_message=str(e), cases=cases, status_dict={},
                               admin_notify="", admin=True)

    # Load status values from API response
    title_status = title_status_res.json()

    # Flag to hide/show the bell icon in the sidebar
    admin_notify = 0

    # add all status values of each case to a dictionary for computing further down
    for status_val in title_status:
        status_dict[status_val['title_number']] = status_val['status']
        # show/hide notification bell
        if status_val['status'] == "proposed_consent_for_discharge":
            admin_notify = 1

    return render_template('app/admin/case_list.html', cases=cases, status_dict=status_dict,
                           admin_notify=admin_notify, admin=True)


@admin.route("/request-issuance", methods=['GET', 'POST'])
@login_required
def request_issuance():
    try:
        # for ajax request
        if request.is_xhr:
            try:
                # Fetch owner from case management
                cases_res = requests.get(
                    current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases/' + request.args['case_reference'],
                    params={"embed": "client"},
                    headers={'Accept': 'application/json'})
                # response
                if cases_res.status_code == 200:
                    case = cases_res.json()
                    case["client"]["type"] = "individual"
                    case_data = {"title_number": request.args['title_number'],
                                 "owner": case['client']}
                    # Make request for issuance call
                    url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + request.args['title_number']
                    response = requests.post(
                        url,
                        data=json.dumps(case_data),
                        headers={'Accept': 'Application/JSON', 'Content-Type': 'Application/JSON'})
                    if response.status_code == 200:
                        return "true"
                    else:
                        return "Error: " + response.text
                else:
                    return "Error: " + cases_res.text

            except requests.exceptions.RequestException:
                return "Conveyancer API is down."

    except Exception as e:
        return e


@admin.route("/draft-sales-agreement", methods=['GET', 'POST'])
@login_required
def draft_sales_agreement():
    if request.args.get('case_reference'):
        session['case_reference'] = str(request.args.get('case_reference'))
    else:
        return render_template('app/admin/draft_sales_agreement.html',
                               error_message="Case reference is a required query parameter", admin=True)
    cases_details = {
        'seller_details': {},
        'buyer_details': {},
        'seller_conveyancer_details': {},
        'buyer_conveyancer_details': {}
    }
    # api call to fetch case details
    cases_res = requests.get(current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases/' + session['case_reference'],
                             params={"embed": "counterparty_id,client,counterparty_conveyancer_contact_id,"
                                              "assigned_staff"},
                             headers={'Accept': 'application/json'})
    # response
    if cases_res.status_code != 200:
        return render_template('app/admin/draft_sales_agreement.html', cases_details=cases_details,
                               error_message="Case not found", admin=True)
    cases_details = cases_res.json()
    if request.method == 'POST':
        # make API call to create agreement state
        title_id = request.form.get('title_id')
        buyer_details = fetch_user_details(request.form.get('buyer_id'))
        buyer_details["type"] = "individual"

        # assign the format the input date is in
        completion_date_obj = datetime.strptime(request.form.get('completion_date'), '%d/%m/%Y')

        # combine date and time of completion
        time_to_add = datetime.strptime(request.form.get('completion_time'), '%H:%M').time()
        completion_date_obj = datetime.combine(completion_date_obj, time_to_add)
        completion_date = datetime.strftime(completion_date_obj, '%Y-%m-%dT%H:%M:%SZ')
        payment_settler = {
            "organisation": current_app.config['PAYMENT_SETTLER_PARTY_ORGANISATION'],
            "locality": current_app.config['PAYMENT_SETTLER_PARTY_LOCALITY'],
            "country": current_app.config['PAYMENT_SETTLER_PARTY_COUNTRY']
        }
        if current_app.config.get('PAYMENT_SETTLER_PARTY_STATE'):
            payment_settler['state'] = current_app.config['PAYMENT_SETTLER_PARTY_STATE']
        if current_app.config.get('PAYMENT_SETTLER_PARTY_ORGANISATIONAL_UNIT'):
            payment_settler['organisational_unit'] = current_app.config['PAYMENT_SETTLER_PARTY_ORGANISATIONAL_UNIT']
        if current_app.config.get('PAYMENT_SETTLER_PARTY_COMMON_NAME'):
            payment_settler['common_name'] = current_app.config['PAYMENT_SETTLER_PARTY_COMMON_NAME']

        contract_data = {
            "buyer_conveyancer": cases_details['counterparty_conveyancer_org'],
            "buyer": buyer_details,
            "completion_date": completion_date,
            "creation_date": datetime.now().strftime('%Y-%m-%d'),
            "contract_rate": request.form.get('contract_rate'),
            "purchase_price": request.form.get('purchase_price'),
            "balance": request.form.get('balance'),
            "balance_currency_code": "GBP",
            "purchase_price_currency_code": "GBP",
            "deposit": request.form.get('deposit'),
            "deposit_currency_code": "GBP",
            "contents_price": 0.0,
            "guarantee": request.form.get('title_guarantee'),
            "contents_price_currency_code": "GBP",
            "payment_settler": payment_settler
        }
        try:
            # draft a sales agreement for a title
            url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_id + '/sales-agreement'
            response = requests.post(url, data=json.dumps(contract_data),
                                     headers={'Accept': 'Application/JSON', 'Content-Type': 'Application/JSON'})

            if response.status_code == 200:
                return redirect(url_for('conveyancer_admin.case_list'))
            else:
                if response.text:
                    error_message = response.text
                else:
                    error_message = "Error: Conveyancer API failed. Could not return a response."
                return render_template('app/admin/draft_sales_agreement.html', title_id=title_id,
                                       error_message=error_message, admin=True)
        except requests.exceptions.RequestException:
            return "Conveyancer API is down."
    else:
        title_id = cases_details['title_number']
        # set values based on whether current case is to sell or buy a property
        if cases_details['case_type'] == "sell":
            fetch_case_details("seller", "buyer", cases_details)
        else:
            fetch_case_details("buyer", "seller", cases_details)

        # DEMO ONLY. Set the completion date to today's date for demo purposes.
        cases_details['completion_date'] = datetime.now().strftime('%d/%m/%Y')

        return render_template('app/admin/draft_sales_agreement.html',
                               title_id=title_id,
                               cases_details=cases_details,
                               admin=True)


@admin.route("/review-sales-agreement", methods=['GET', 'POST'])
@login_required
def review_sales_agreement():
    # save case ref in session so that its available on error redirects
    if request.args.get('case_reference'):
        session['case_reference'] = str(request.args.get('case_reference'))

    # form post
    if request.method == 'POST':
        try:
            title_id = request.form['title_id']

            # api to fetch buyer's conveyancer details
            url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_id + '/sales-agreement'
            agreement_res = requests.get(url, headers={'Accept': 'application/json'})
            agreement_obj = agreement_res.json()
            agreement_approval_data = {"action": "approve",
                                       "signatory": agreement_obj['buyer_conveyancer']
                                       }
            # approve agreement api call
            url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_id + '/sales-agreement'
            response = requests.put(url, data=json.dumps(agreement_approval_data),
                                    headers={'Accept': 'Application/JSON', 'Content-Type': 'Application/JSON'})
            if response.status_code == 200:
                return redirect(url_for('conveyancer_admin.case_list'))
            else:
                return redirect(url_for('conveyancer_admin.review_sales_agreement',
                                        error_message='Error: ' + response.text))
        except Exception as e:
            return str(e)

    if request.method == 'GET':
        cases_details = {}
        # get case details
        url = current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases/' + session['case_reference']
        case_details_res = requests.get(url, params={"embed": "counterparty_id,client,"
                                                              "counterparty_conveyancer_contact_id,assigned_staff"},
                                        headers={'Accept': 'application/json'})
        if case_details_res.status_code == 200:
            cases_details = case_details_res.json()
            # if title number is not updated in the case redirect to case list
            if cases_details['title_number']:
                title_id = cases_details['title_number']
            else:
                return redirect(url_for('conveyancer_admin.case_list',
                                        error_message='Error: Title not found in the case'))

            if cases_details['case_type'] == "sell":
                fetch_case_details("seller", "buyer", cases_details)
            else:
                fetch_case_details("buyer", "seller", cases_details)
        # make API call to fetch agreement values
        url = '{0}/titles/{1}/sales-agreement'.format(
            current_app.config['CONVEYANCER_API_URL'],
            cases_details['title_number'])
        agreement_details_response = requests.get(url, headers={'Accept': 'application/json'})

        if agreement_details_response.status_code == 200:
            agreement_detail = agreement_details_response.json()
            obj_date = datetime.strptime(agreement_detail['completion_date'], '%Y-%m-%dT%H:%M:%S')
            agreement_detail['completion_date'] = datetime.strftime(obj_date, '%d %B %Y %H:%M')
            if agreement_detail['latest_update_date']:
                update_date = datetime.strptime(agreement_detail['latest_update_date'], '%Y-%m-%dT%H:%M:%S.%f')
                agreement_detail['latest_update_date_time'] = datetime.strftime(update_date, '%d/%m/%Y %H:%M:%S')
            else:
                agreement_detail['latest_update_date_time'] = ""

            agreement_detail['purchase_price'] = numbers.format_currency(
                agreement_detail['purchase_price'],
                agreement_detail['purchase_price_currency_code'])
            agreement_detail['deposit'] = numbers.format_currency(
                agreement_detail['deposit'],
                agreement_detail['deposit_currency_code'])
            agreement_detail['balance'] = numbers.format_currency(
                agreement_detail['balance'],
                agreement_detail['balance_currency_code'])
            agreement_detail['deposit_currency_code'] = numbers.get_currency_symbol(
                agreement_detail['deposit_currency_code'])
            agreement_detail['balance_currency_code'] = numbers.get_currency_symbol(
                agreement_detail['balance_currency_code'])
            agreement_detail['contents_price_currency_code'] = numbers.get_currency_symbol(
                agreement_detail['contents_price_currency_code'])
            agreement_detail['purchase_price_currency_code'] = numbers.get_currency_symbol(
                agreement_detail['purchase_price_currency_code'])
            return render_template('app/admin/review_sales_agreement.html',
                                   agreement_details=agreement_detail,
                                   title_details=cases_details,
                                   title_id=title_id,
                                   admin=True)
        else:
            return render_template('app/admin/review_sales_agreement.html',
                                   error_message="Title agreement does not exist",
                                   admin=True)


@admin.route("/add-new-charge-restriction", methods=['GET', 'POST'])
@login_required
def add_new_charge_restriction():
    if request.args.get('case_reference'):
        session['case_reference'] = str(request.args.get('case_reference'))

    # get title number from case reference
    title_number = get_title_number(session['case_reference'])

    # if title number not found go to case list
    if not title_number:
        return redirect(url_for('conveyancer_admin.case_list',
                                error_message='Error: Case has no title linked to it.'))

    # Form posted
    if request.method == 'POST':
        lender_party = {
            "organisation": current_app.config['BUYER_LENDER_PARTY_ORGANISATION'],
            "locality": current_app.config['BUYER_LENDER_PARTY_LOCALITY'],
            "country": current_app.config['BUYER_LENDER_PARTY_COUNTRY']
        }
        if current_app.config.get('BUYER_LENDER_PARTY_STATE'):
            lender_party['state'] = current_app.config['BUYER_LENDER_PARTY_STATE']
        if current_app.config.get('BUYER_LENDER_PARTY_ORGANISATIONAL_UNIT'):
            lender_party['organisational_unit'] = current_app.config['BUYER_LENDER_PARTY_ORGANISATIONAL_UNIT']
        if current_app.config.get('BUYER_LENDER_PARTY_COMMON_NAME'):
            lender_party['common_name'] = current_app.config['BUYER_LENDER_PARTY_COMMON_NAME']

        data = {
            "restriction_id": "NA",
            "restriction_type": "CBCR",
            "restriction_text": request.form.get('restriction_text'),
            "consenting_party": lender_party,
            "signed_actions": "add",
            "date": request.form.get('date'),
            "charge": {
                "date": request.form.get('date'),
                "lender": lender_party,
                "amount": request.form.get('amount'),
                "amount_currency_code": request.form.get('amount_currency')
            }
        }
        try:
            url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_number + '/restrictions'
            add_restriction_res = requests.post(url, data=json.dumps(data),
                                                headers={'Accept': 'application/json',
                                                         'Content-Type': 'Application/JSON'})
            if add_restriction_res.status_code == 200:
                return redirect(url_for('conveyancer_admin.case_list'))
            else:
                if add_restriction_res.text:
                    error_message = add_restriction_res.text
                else:
                    error_message = "Error: Conveyancer API failed. Could not return a response."
                return redirect(url_for('conveyancer_admin.case_list', error_message=error_message))
        except requests.exceptions.RequestException:
            return "Conveyancer API is down."
    else:
        # Fetch agreement completion date and purchase amount
        url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_number + '/sales-agreement'
        agreement_res = requests.get(url, headers={'Accept': 'application/json'})
        agreement_obj = agreement_res.json()
        title_charges_res = requests.get(current_app.config['CASE_MANAGEMENT_API_URL'] + '/restrictions',
                                         params={'type': 'CBCR'},
                                         headers={'Accept': 'application/json'})
        # get buyer lender name
        buyer_lender = "Gringott's Bank"

        title_charges = {}
        if title_charges_res.status_code == 200:
            title_charges = title_charges_res.json()
            # change date and amount formats
            for title_charge in title_charges:
                # assign the format the input date is in
                completion_date_obj = datetime.strptime(agreement_obj['completion_date'], '%Y-%m-%dT%H:%M:%S')
                title_charge['date_unformatted'] = datetime.strftime(completion_date_obj, '%Y-%m-%dT%H:%M:%S')
                title_charge['date'] = datetime.strftime(completion_date_obj, '%d %B %Y')
                title_charge['buyer_lender'] = buyer_lender
                title_charge['amount_currency'] = agreement_obj['balance_currency_code']
                title_charge['amount'] = agreement_obj["balance"]
                title_charge['amount_display'] = numbers.format_currency(agreement_obj["balance"],
                                                                         agreement_obj['balance_currency_code'])
                placeholders = [
                    {"placeholder_str": "*CD*", "field": "date"},
                    {"placeholder_str": "*CP*", "field": "buyer_lender"}
                ]

                # loop over placeholders to replace them
                for placeholder in placeholders:
                    if placeholder['field'] in title_charge:
                        restriction_text = title_charge['restriction_text']
                        title_charge['restriction_text'] = restriction_text.replace(
                            placeholder['placeholder_str'], str(title_charge[placeholder['field']]))
        return render_template('app/admin/add_charge_restriction.html', title_charge=title_charge, admin=True)


@admin.route("/request-mortgage-discharge", methods=['GET', 'POST'])
@login_required
def request_mortgage_discharge():
    title_number = request.args.get('title_number')
    url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + title_number + '/charges'
    response = requests.put(url, data=json.dumps({"action": "request_discharge"}),
                            headers={'Accept': 'Application/JSON', 'Content-Type': 'Application/JSON'})
    if response.status_code == 200:
        return redirect(url_for('conveyancer_admin.case_list'))
    else:
        return redirect(url_for('conveyancer_admin.case_list', error_message="Error:" + response.text))


@admin.route("/title-details")
@login_required
def title_details_popup():
    error = None

    # Load extra hardcoded details from flat file
    extras = None
    if os.path.isfile(extras_filepath):
        with open(extras_filepath) as json_file:
            extras = json.load(json_file)

    for price_idx, price in enumerate(extras['price_history']):
        extras['price_history'][price_idx]['price_pretty'] = numbers.format_currency(
            price['amount'] / 100,
            price['currency_code']
        ).replace(".00", "")

        date_pretty = datetime.fromtimestamp(price['date']).strftime('%d %B %Y')
        extras['price_history'][price_idx]['date_pretty'] = date_pretty

        date_full_pretty = datetime.fromtimestamp(price['date']).strftime('%d %B %Y %H:%M:%S')
        extras['price_history'][price_idx]['date_full_pretty'] = date_full_pretty

    try:
        url = current_app.config['CONVEYANCER_API_URL'] + '/titles/' + request.args.get('title_number')
        response = requests.get(url, data=json.dumps({"action": "request_discharge"}),
                                headers={'Accept': 'Application/JSON', 'Content-Type': 'Application/JSON'})
        if response.status_code == 200:
            title_data = response.json()
            return render_template('app/admin/title_details.html', extras=extras, title_data=title_data)
        else:
            error = "Error: " + response.text
    except requests.exceptions.RequestException:
        error = "Could not connect to Conveyancer API"
    return render_template('app/admin/title_details.html', extras=extras, error_message=error)


@admin.route("/request-client-id", methods=['GET', 'POST'])
@login_required
def request_client_id():
    if request.method == 'POST':
        try:
            response = requests.post(
                current_app.config['CONVEYANCER_API_URL'] + '/yoti-signin-request',
                headers={'Accept': 'Application/JSON', 'Content-Type': 'Application/JSON'},
                data=json.dumps({
                    "client_phone_number": '+44' + request.form.get('client_phone'),
                    "client_full_name": request.form.get('client_name'),
                    "user_callback_url": url_for('auth.register_yoti', _external=True)
                })
            )
            if not response.status_code == 200:
                return "Conveyancer API returned " + str(response.status_code)
        except requests.exceptions.RequestException:
            return "Conveyancer API is down."
        return redirect(url_for('conveyancer_admin.case_list'))
    else:
        return render_template('app/admin/request_id.html')


def get_title_number(case_ref):
    url = current_app.config['CASE_MANAGEMENT_API_URL'] + '/cases/' + case_ref
    title_details_res = requests.get(url, headers={'Accept': 'application/json'})
    if title_details_res.status_code == 200:
        cases_details = title_details_res.json()
        return cases_details['title_number']
    else:
        return None


def fetch_case_details(client, counter, cases_details):
    cases_details[client + '_details'] = cases_details['client']
    cases_details[counter + '_details'] = cases_details['counterparty']
    assigned_staff = cases_details['assigned_staff']
    cases_details[client + '_conveyancer_details'] = {
        "email": assigned_staff['email_address'],
        "name": assigned_staff['first_name'] + " " + assigned_staff['last_name']
    }
    conveyancer_details = cases_details['counterparty_conveyancer_contact']
    cases_details[counter + '_conveyancer_details'] = {
        "email": conveyancer_details['email_address'],
        "name": conveyancer_details['first_name'] + " " + conveyancer_details['last_name']
    }


def fetch_user_details(user_id):
    client_res = requests.get(current_app.config['CASE_MANAGEMENT_API_URL'] + '/users/' + str(user_id),
                              headers={'Accept': 'application/json'})
    if client_res.status_code == 200:
        return client_res.json()
    else:
        return None
