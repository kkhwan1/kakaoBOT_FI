#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Playwright를 사용한 영화 순위 조회
실제 챗봇에서 사용하려면 이 함수를 import해서 사용
"""

def movie_rank_with_playwright():
    """Playwright로 KOBIS 실시간 박스오피스 가져오기"""
    try:
        from playwright.sync_api import sync_playwright
        from datetime import datetime
        
        with sync_playwright() as p:
            # 브라우저 실행 (headless=True로 백그라운드 실행)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # KOBIS 일일 박스오피스 페이지 접속
            page.goto("https://kobis.or.kr/kobis/business/stat/boxs/findDailyBoxOfficeList.do")
            
            # 페이지 로딩 대기
            page.wait_for_selector('#tbody_0', timeout=5000)
            
            # 데이터 추출
            movies = page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('#tbody_0 tr');
                    const movies = [];
                    
                    rows.forEach((row) => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 10) {
                            const rank = cells[0].textContent.trim();
                            const titleLink = cells[1].querySelector('a');
                            const title = titleLink ? titleLink.textContent.trim() : cells[1].textContent.trim();
                            const audience = cells[7].textContent.trim().replace(/\\s+/g, '').replace(/,/g, '');
                            const cumulative = cells[9].textContent.trim().replace(/\\s+/g, '').replace(/,/g, '');
                            
                            movies.push({
                                rank: rank,
                                title: title,
                                audience: audience,
                                cumulative: cumulative
                            });
                        }
                    });
                    
                    return movies.slice(0, 10);
                }
            """)
            
            browser.close()
            
            if movies:
                # 현재 시간 정보 추가
                from datetime import datetime, timedelta
                now = datetime.now()
                yesterday = now - timedelta(days=1)
                
                # 카카오톡 호환 - TOP 10 표시, 콤마 추가
                send_msg = f"📽️ 일일 박스오피스 TOP10\n"
                send_msg += f"📅 {yesterday.strftime('%Y년 %m월 %d일')} 기준\n\n"
                
                for movie in movies[:10]:  # TOP 10
                    rank = movie['rank']
                    title = movie['title']
                    send_msg += f"{rank}위. {title}\n"
                    
                    # 일일 관객수와 누적 관객수 표시
                    audience_str = ""
                    if movie['audience']:
                        try:
                            aud_num = int(movie['audience'])
                            aud_formatted = f"{aud_num:,}"
                            audience_str = f"일일 {aud_formatted}명"
                        except:
                            audience_str = f"일일 {movie['audience']}명"
                    
                    if movie['cumulative']:
                        try:
                            cum_num = int(movie['cumulative'])
                            cum_formatted = f"{cum_num:,}"
                            if audience_str:
                                send_msg += f"{audience_str} / 누적 {cum_formatted}명\n"
                            else:
                                send_msg += f"누적 {cum_formatted}명\n"
                        except:
                            if audience_str:
                                send_msg += f"{audience_str} / 누적 {movie['cumulative']}명\n"
                            else:
                                send_msg += f"누적 {movie['cumulative']}명\n"
                    elif audience_str:
                        send_msg += f"{audience_str}\n"
                    
                    send_msg += "\n"
                
                return send_msg.strip()
            
    except ImportError:
        return "⚠️ Playwright가 설치되지 않았습니다.\npip install playwright\nplaywright install chromium"
    except Exception as e:
        return f"❌ 조회 실패: {str(e)}"

# 간단한 버전 - selenium 사용
def movie_rank_with_selenium():
    """Selenium으로 네이버 영화 박스오피스 가져오기"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from datetime import datetime
        
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 백그라운드 실행
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # 네이버 영화 박스오피스
            driver.get("https://movie.naver.com/movie/sdb/rank/rmovie.naver")
            
            # 테이블 로딩 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.list_ranking"))
            )
            
            # 영화 목록 가져오기
            movies = driver.find_elements(By.CSS_SELECTOR, "table.list_ranking tbody tr")
            
            if movies:
                send_msg = "🍿 네이버 실시간 박스오피스 TOP 10\n"
                send_msg += f"📅 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} 기준\n"
                send_msg += "="*30 + "\n\n"
                
                count = 0
                for movie in movies[:10]:
                    try:
                        title_elem = movie.find_element(By.CSS_SELECTOR, ".title a")
                        if title_elem:
                            count += 1
                            title = title_elem.text
                            
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
                            try:
                                rating = movie.find_element(By.CSS_SELECTOR, ".point").text
                                send_msg += f"   ⭐ 평점: {rating}\n"
                            except:
                                pass
                            
                            send_msg += "\n"
                    except:
                        continue
                
                if count > 0:
                    send_msg += "📊 출처: 네이버 영화"
                    return send_msg
                    
        finally:
            driver.quit()
            
    except ImportError:
        return "⚠️ Selenium이 설치되지 않았습니다.\npip install selenium"
    except Exception as e:
        return f"❌ 조회 실패: {str(e)}"

if __name__ == "__main__":
    # 테스트
    print("Playwright 버전 테스트:")
    print(movie_rank_with_playwright())
    print("\n" + "="*50 + "\n")
    print("Selenium 버전 테스트:")
    print(movie_rank_with_selenium())