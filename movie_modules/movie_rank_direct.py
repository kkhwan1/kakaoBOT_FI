#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
requests를 사용한 직접 KOBIS 스크래핑
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def movie_rank_direct_kobis():
    """requests로 KOBIS 페이지 직접 스크래핑"""
    try:
        # 어제 날짜 설정 (KOBIS는 주로 전일 데이터 제공)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        
        # KOBIS 일일 박스오피스 페이지
        url = "https://kobis.or.kr/kobis/business/stat/boxs/findDailyBoxOfficeList.do"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }
        
        # POST 요청으로 데이터 가져오기
        data = {
            'loadEnd': '0',
            'searchType': 'search',
            'sSearchFrom': yesterday,
            'sSearchTo': yesterday,
            'sMultiMovieYn': '',
            'sRepNationCd': '',
            'sWideAreaCd': ''
        }
        
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 테이블 찾기
            table = soup.find('table', {'class': 'boardList03'})
            if not table:
                table = soup.find('table', {'summary': '박스오피스 리스트'})
            
            if table:
                movies = []
                rows = table.find('tbody').find_all('tr')
                
                for row in rows[:10]:
                    cells = row.find_all('td')
                    if len(cells) >= 10:
                        rank = cells[0].get_text(strip=True)
                        
                        # 영화 제목 추출
                        title_elem = cells[1].find('a')
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                        else:
                            title = cells[1].get_text(strip=True)
                        
                        # 관객수 정보
                        audience = cells[7].get_text(strip=True) if len(cells) > 7 else ""
                        cumulative = cells[9].get_text(strip=True) if len(cells) > 9 else ""
                        
                        movies.append({
                            'rank': rank,
                            'title': title,
                            'audience': audience,
                            'cumulative': cumulative
                        })
                
                if movies:
                    send_msg = "🍿 KOBIS 일일 박스오피스 TOP 10\n"
                    send_msg += f"📅 {yesterday[:4]}년 {yesterday[4:6]}월 {yesterday[6:]}일 기준\n"
                    send_msg += "="*30 + "\n\n"
                    
                    for movie in movies:
                        rank = movie['rank']
                        if rank == "1":
                            emoji = "🥇"
                        elif rank == "2":
                            emoji = "🥈"
                        elif rank == "3":
                            emoji = "🥉"
                        else:
                            emoji = f"{rank}️⃣"
                        
                        send_msg += f"{emoji} {movie['title']}\n"
                        
                        if movie['audience']:
                            send_msg += f"   일일: {movie['audience']}명"
                        if movie['cumulative']:
                            send_msg += f" | 누적: {movie['cumulative']}명"
                        if movie['audience'] or movie['cumulative']:
                            send_msg += "\n"
                        
                        send_msg += "\n"
                    
                    send_msg += "📊 출처: KOBIS (영화진흥위원회)"
                    return send_msg
        
        return None
        
    except Exception as e:
        print(f"KOBIS 직접 스크래핑 오류: {e}")
        return None

def movie_rank_naver():
    """네이버 영화 박스오피스"""
    try:
        url = "https://movie.naver.com/movie/sdb/rank/rmovie.naver"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        movies = soup.select('table.list_ranking tbody tr')
        if movies:
            send_msg = "🍿 네이버 박스오피스 TOP 10\n"
            send_msg += f"📅 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} 기준\n"
            send_msg += "="*30 + "\n\n"
            
            count = 0
            for movie in movies:
                title_elem = movie.select_one('.title a')
                if title_elem and count < 10:
                    count += 1
                    title = title_elem.get_text(strip=True)
                    
                    # 순위별 이모지
                    if count == 1:
                        emoji = '🥇'
                    elif count == 2:
                        emoji = '🥈'
                    elif count == 3:
                        emoji = '🥉'
                    else:
                        emoji = f'{count}️⃣'
                    
                    send_msg += f"{emoji} {title}\n"
                    
                    # 평점 정보
                    rating_elem = movie.select_one('.point')
                    if rating_elem:
                        rating = rating_elem.get_text(strip=True)
                        send_msg += f"   ⭐ 평점: {rating}\n"
                    
                    send_msg += "\n"
            
            if count > 0:
                send_msg += "📊 출처: 네이버 영화"
                return send_msg
        
        return None
        
    except Exception as e:
        print(f"네이버 영화 조회 오류: {e}")
        return None

if __name__ == "__main__":
    # 테스트
    print("KOBIS 직접 스크래핑 테스트:")
    result = movie_rank_direct_kobis()
    if result:
        print(result)
    else:
        print("KOBIS 조회 실패")
    
    print("\n" + "="*50 + "\n")
    
    print("네이버 영화 테스트:")
    result = movie_rank_naver()
    if result:
        print(result)
    else:
        print("네이버 조회 실패")