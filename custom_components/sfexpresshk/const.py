"""Constants for the SF Express HK integration."""

DOMAIN = "sfexpresshk"

CONF_PHONE_NUMBER = "mobile"
CONF_MEMBER_ID = "member_id"

# API Constants
API_REGION_CODE = "HK"
API_LANGUAGE_CODE = "tc"
API_USER_AGENT = "okhttp/4.9.1"
API_CONTENT_TYPE = "application/json"
API_ACCEPT_ENCODING = "gzip"
API_CARRIER = ""

# API Headers

# API Endpoints
API_LOGIN_ENDPOINT = "https://hmto.sf-express.com/cx-app-member/member/app/user/login"
API_QUERY_USER_ENDPOINT = "https://hmto.sf-express.com/cx-app-member/member/app/user/queryUserById"
API_LIST_WAYBILL_ENDPOINT = "https://hmto.sf-express.com/proxy/query/queryBillRestService/listWayBill"
API_QUERY_ROUTE_ENDPOINT = "https://hmto.sf-express.com/cx-app-query/query/app/waybillNo/queryWaybillByBNo"
API_PICKUP_CODE_ENDPOINT = "https://hmto.sf-express.com/cx-app-order/order/app/recCode/fcRecCode"

# Status codes
STATUS_DELIVERED = "4"
STATUS_DIVERTED = "9"
