import time
import urllib.parse
import random
import base64
import hmac
import hashlib

import fn

def search_ad(keyword):
    BASE_URL = 'https://api.searchad.naver.com'

    # 네이버 API 사용량 분산을 위해 여러개중 랜덤으로 선택
    api_list = [
        {'api_key':'re5HGzSIDVs6_q22qg7a', 'secret_key':'AzARtMmHyh', 'customer_id':'CUSTOMER_ID'},
        {'api_key':'re5HGzSIDVs6_q22qg7a', 'secret_key':'AzARtMmHyh', 'customer_id':'CUSTOMER_ID'},
    ]
    api = random.choice(api_list)
    api_key = api['api_key']
    secret_key = api['secret_key']
    customer_id = api['customer_id']

    uri = '/keywordstool'
    url = BASE_URL + uri
    method = 'GET'
    keyword = keyword.replace(' ', '')
    params = {'hintKeywords': keyword, 'showDetail': '1'}
    
    timestamp = str(round(time.time() * 1000))
    message = "{}.{}.{}".format(timestamp, method, uri)
    hash = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256)
    hash.hexdigest()
    signature = base64.b64encode(hash.digest()).decode('utf-8')

    headers = {
        'Content-Type': 'application/json; charset=UTF-8', 
        'X-Timestamp': timestamp, 
        'X-API-KEY': api_key, 
        'X-Customer': customer_id, 
        'X-Signature': signature
    }
    data = fn.request(url, method, "json", params, headers)
    
    if not data or not isinstance(data, dict) or 'keywordList' not in data or not data['keywordList']:
        return None, 0, 0, 0
    
    rel_keyword = ''
    pc_cnt = 0
    mo_cnt = 0
    total_cnt = 0
    
    try:
        for k in data['keywordList']:
            if k['relKeyword'] != keyword.upper():
                if rel_keyword == '':
                    rel_keyword = k['relKeyword']
                else:
                    # 10개까지만 표시
                    if len(rel_keyword.split(', ')) < 10:
                        rel_keyword += ', ' + k['relKeyword']
            
            if k['relKeyword'] == keyword.upper():
                pc_cnt = k['monthlyPcQcCnt'] if k['monthlyPcQcCnt'] != '< 10' else 0
                mo_cnt = k['monthlyMobileQcCnt'] if k['monthlyMobileQcCnt'] != '< 10' else 0
                # 숫자 타입 변환
                try:
                    pc_cnt = int(pc_cnt) if pc_cnt != 0 else 0
                    mo_cnt = int(mo_cnt) if mo_cnt != 0 else 0
                    total_cnt = pc_cnt + mo_cnt
                except (ValueError, TypeError):
                    pc_cnt = mo_cnt = total_cnt = 0
    except Exception as e:
        print(f"키워드 데이터 파싱 오류: {e}")
        return None, 0, 0, 0
    
    return rel_keyword, pc_cnt, mo_cnt, total_cnt



def search_blog(keyword):

    # 네이버 API 사용량 분산을 위해 여러개중 랜덤으로 선택
    client_list = [
        {'client_id': 're5HGzSIDVs6_q22qg7a', 'client_secret': 'AzARtMmHyh'},
        {'client_id': 're5HGzSIDVs6_q22qg7a', 'client_secret': 'AzARtMmHyh'},
        {'client_id': 're5HGzSIDVs6_q22qg7a', 'client_secret': 'AzARtMmHyh'},
        {'client_id': 're5HGzSIDVs6_q22qg7a', 'client_secret': 'AzARtMmHyh'},
    ]
    client = random.choice(client_list)
    client_id = client['client_id']
    client_secret = client['client_secret']

    encText = urllib.parse.quote(keyword)
    url = "https://openapi.naver.com/v1/search/blog?query=" + encText + "&display=8"  # 8개 결과 요청 
    headers = {
        'X-Naver-Client-Id': client_id,
        'X-Naver-Client-Secret': client_secret
    }
    
    try:
        data = fn.request(url, 'GET', 'json', None, headers)
        return data
    except Exception as e:
        print(f"블로그 검색 API 오류: {e}")
        return None
