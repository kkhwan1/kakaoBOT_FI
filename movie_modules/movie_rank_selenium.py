#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Selenium을 사용한 영화 순위 조회 (Playwright 대체용)
"""

def movie_rank_with_selenium():
    """Selenium으로 KOBIS 실시간 박스오피스 가져오기"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from datetime import datetime
        import time
        
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 백그라운드 실행
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        # User-Agent 설정
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # KOBIS 일일 박스오피스 페이지 접속
            print("KOBIS 페이지 접속 중...")
            driver.get("https://kobis.or.kr/kobis/business/stat/boxs/findDailyBoxOfficeList.do")
            
            # 페이지 로딩 대기
            time.sleep(3)  # 명시적 대기
            
            # 테이블 로딩 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "tbody_0"))
            )
            
            # JavaScript로 데이터 추출
            movies = driver.execute_script("""
                var rows = document.querySelectorAll('#tbody_0 tr');
                var movies = [];
                
                for (var i = 0; i < rows.length && i < 10; i++) {
                    var cells = rows[i].querySelectorAll('td');
                    if (cells.length >= 10) {
                        var rank = cells[0].textContent.trim();
                        var titleLink = cells[1].querySelector('a');
                        var title = titleLink ? titleLink.textContent.trim() : cells[1].textContent.trim();
                        var audience = cells[7].textContent.trim().replace(/\\s+/g, '').replace(/,/g, '');
                        var cumulative = cells[9].textContent.trim().replace(/\\s+/g, '').replace(/,/g, '');
                        
                        movies.push({
                            rank: rank,
                            title: title,
                            audience: audience,
                            cumulative: cumulative
                        });
                    }
                }
                
                return movies;
            """)
            
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
                
        finally:
            driver.quit()
            
    except ImportError as e:
        print(f"Selenium import 오류: {e}")
        return None
    except Exception as e:
        print(f"Selenium 영화 순위 조회 오류: {e}")
        return None

if __name__ == "__main__":
    # 테스트
    print("Selenium 버전 테스트:")
    result = movie_rank_with_selenium()
    if result:
        print(result)
    else:
        print("조회 실패")