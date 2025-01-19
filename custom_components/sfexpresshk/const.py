"""Constants for the SF Express HK integration."""

DOMAIN = "sfexpresshk"

CONF_PHONE_NUMBER = "mobile"
CONF_MEMBER_ID = "member_id"
CONF_SFBUY_TICKET = "sfbuy_ticket"

# API Constants
API_REGION_CODE = "HK"
API_LANGUAGE_CODE = "tc"
API_USER_AGENT = "okhttp/4.9.1"
API_CONTENT_TYPE = "application/json"
API_ACCEPT_ENCODING = "gzip"
API_CARRIER = ""

# SFBuy API Constants
SFBUY_USER_AGENT = "Mozilla/5.0 (Linux; Android 15; Pixel 7 Build/BP11.241121.010; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.200 Mobile Safari/537.36 mediaCode=SFEXPRESSAPP-Android-HMTO&lang=tc&regionCode=HK"
SFBUY_ACCEPT_ENCODING = "gzip, deflate, br, zstd"

# API Headers
SFBUY_HEADERS = {
    "Connection": "keep-alive",
    "gjUtmCampaign": "",
    "sec-ch-ua-platform": "Android",
    "sec-ch-ua": '"Android WebView";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "order-channel": "3",
    "Accept": "application/json, text/plain, */*",
    "sfbuy-access-source": "app",
    "X-Requested-With": "com.sf.hmto",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://m.sfbuy.com/",
    "Accept-Language": "en-HK,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": SFBUY_ACCEPT_ENCODING,
    "User-Agent": SFBUY_USER_AGENT,
}

# API Endpoints
API_LOGIN_ENDPOINT = "https://hmto.sf-express.com/cx-app-member/member/app/user/login"
API_QUERY_USER_ENDPOINT = "https://hmto.sf-express.com/cx-app-member/member/app/user/queryUserById"
API_LIST_WAYBILL_ENDPOINT = "https://hmto.sf-express.com/proxy/query/queryBillRestService/listWayBill"
API_QUERY_ROUTE_ENDPOINT = "https://hmto.sf-express.com/cx-app-query/query/app/waybillNo/queryWaybillByBNo"
API_SFBUY_COUNT_ENDPOINT = "https://m.sfbuy.com/pkg/count"
API_PICKUP_CODE_ENDPOINT = "https://hmto.sf-express.com/cx-app-order/order/app/recCode/fcRecCode"
