import os
# RULES OF CONFIG:
# 1. No region specific code. Regions are defined by setting the OS environment variables appropriately to build up the
# desired behaviour.
# 2. No use of defaults when getting OS environment variables. They must all be set to the required values prior to the
# app starting.
# 3. This is the only file in the app where os.environ should be used.


# For logging
FLASK_LOG_LEVEL = os.environ['LOG_LEVEL']

# For health route
COMMIT = os.environ['COMMIT']

# This APP_NAME variable is to allow changing the app name when the app is running in a cluster. So that
# each app in the cluster will have a unique name.
APP_NAME = os.environ['APP_NAME']

MAX_HEALTH_CASCADE = os.environ['MAX_HEALTH_CASCADE']
# Following is an example of building the dependency structure used by the cascade route
# SELF can be used to demonstrate how it works (i.e. it will call it's own cascade
# route until MAX_HEALTH_CASCADE is hit)
# SELF = "http://localhost:8080"
# DEPENDENCIES = {"SELF": SELF}

# Secret key for CSRF
SECRET_KEY = os.environ['SECRET_KEY']

# Content security policy mode
# Can be either 'full' or 'report-only'
# 'full' will action the CSP and block violations
# 'report-only' will log but not block violations
# It is recommended to run in report-only mode for a while and monitor the logs
# to ensure that all violations are cleaned up to prevent your app from breaking
# when you switch it on fully
CONTENT_SECURITY_POLICY_MODE = 'report-only'  # os.environ['CONTENT_SECURITY_POLICY_MODE']

# Static assets mode
# Can be either 'development' or 'production'
# 'development' will:
#   - Not gzip static assets
#   - Set far *past* expiry headers on static asset requests to prevent your browser from caching them
#   - Not add cachebusters to static asset query strings
# 'production' will:
#   - gzip static assets
#   - Set far *future* expiry headers on static asset requests to force browsers to cache for a long time
#   - Add cachebusters to static asset query strings to invalidate browsers' caches when necessary
STATIC_ASSETS_MODE = os.environ['STATIC_ASSETS_MODE']
CONVEYANCER_API_URL = os.environ['CONVEYANCER_API_URL']
APP_USER = os.environ['APP_USER']
CASE_MANAGEMENT_API_URL = os.environ['CASE_MANAGEMENT_API_URL']
PAYMENT_SETTLER_PARTY_ORGANISATION = os.environ['PAYMENT_SETTLER_PARTY_ORGANISATION']
PAYMENT_SETTLER_PARTY_LOCALITY = os.environ['PAYMENT_SETTLER_PARTY_LOCALITY']
PAYMENT_SETTLER_PARTY_COUNTRY = os.environ['PAYMENT_SETTLER_PARTY_COUNTRY']
PAYMENT_SETTLER_PARTY_STATE = os.environ.get('PAYMENT_SETTLER_PARTY_STATE')
PAYMENT_SETTLER_PARTY_ORGANISATIONAL_UNIT = os.environ.get('PAYMENT_SETTLER_PARTY_ORGANISATIONAL_UNIT')
PAYMENT_SETTLER_PARTY_COMMON_NAME = os.environ.get('PAYMENT_SETTLER_PARTY_COMMON_NAME')
BUYER_LENDER_PARTY_ORGANISATION = os.environ['BUYER_LENDER_PARTY_ORGANISATION']
BUYER_LENDER_PARTY_LOCALITY = os.environ['BUYER_LENDER_PARTY_LOCALITY']
BUYER_LENDER_PARTY_COUNTRY = os.environ['BUYER_LENDER_PARTY_COUNTRY']
BUYER_LENDER_PARTY_STATE = os.environ.get('BUYER_LENDER_PARTY_STATE')
BUYER_LENDER_PARTY_ORGANISATIONAL_UNIT = os.environ.get('BUYER_LENDER_PARTY_ORGANISATIONAL_UNIT')
BUYER_LENDER_PARTY_COMMON_NAME = os.environ.get('BUYER_LENDER_PARTY_COMMON_NAME')
