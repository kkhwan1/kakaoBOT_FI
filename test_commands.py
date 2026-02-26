import json
import requests

url = 'https://seal-app-dk72t.ondigitalocean.app/api/kakaotalk'

# 테스트할 명령어 목록
commands = [
    ('/테스트', '테스트'),
    ('/시간', '시간'),
    ('/명령어', '명령어'),
    ('/날씨 서울', '날씨'),
    ('/금값', '금값'),
    ('/환율', '환율'),
    ('/주식 삼성전자', '주식'),
    ('/로또', '로또'),
    ('/실시간검색어', '실시간검색어'),
    ('/뉴스', '뉴스'),
    ('/칼로리 사과', '칼로리'),
    ('/운세', '운세'),
    ('/전갈자리', '전갈자리'),
    ('/지도 강남역', '지도'),
]

print('=== 카카오톡 봇 API 명령어 테스트 ===')
print()

results = {'success': 0, 'fail': 0, 'errors': []}

for cmd, desc in commands:
    try:
        resp = requests.post(url, json={'room': '테스트방', 'sender': '테스터', 'msg': cmd}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('is_reply') and data.get('reply_msg'):
                msg = data['reply_msg']
                if len(msg) > 50:
                    msg = msg[:50] + '...'
                print(f'✅ {cmd}: {msg}')
                results['success'] += 1
            else:
                print(f'⚠️ {cmd}: 응답 없음')
                results['fail'] += 1
        else:
            print(f'❌ {cmd}: HTTP {resp.status_code}')
            results['errors'].append(f'{cmd}: HTTP {resp.status_code}')
    except Exception as e:
        err_str = str(e)[:50]
        print(f'❌ {cmd}: {err_str}')
        results['errors'].append(f'{cmd}: {err_str}')

print()
print('=== 결과 요약 ===')
print(f'성공: {results["success"]}')
print(f'실패: {results["fail"]}')
print(f'오류: {len(results["errors"])}')
if results['errors']:
    print('오류 목록:')
    for err in results['errors']:
        print(f'  - {err}')
