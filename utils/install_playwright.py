#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Playwright 설치 확인 및 브라우저 설치 스크립트
"""

import subprocess
import sys

def install_playwright():
    """Playwright 및 브라우저 설치"""
    try:
        # playwright 패키지 설치
        print("Playwright 패키지 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        
        # 브라우저 설치
        print("\nPlaywright 브라우저 설치 중...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        
        print("\n✅ Playwright 설치 완료!")
        
        # 테스트
        print("\n테스트 중...")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.google.com")
            title = page.title()
            browser.close()
            print(f"✅ 테스트 성공! Google 페이지 타이틀: {title}")
            
    except Exception as e:
        print(f"❌ 설치 실패: {e}")
        print("\n대안: Selenium을 사용하세요")
        print("pip install selenium")

def install_selenium():
    """Selenium 설치"""
    try:
        print("Selenium 패키지 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
        
        print("\n✅ Selenium 설치 완료!")
        print("\n⚠️ 주의: Chrome 브라우저와 ChromeDriver가 필요합니다.")
        print("ChromeDriver 다운로드: https://chromedriver.chromium.org/")
        
    except Exception as e:
        print(f"❌ Selenium 설치 실패: {e}")

if __name__ == "__main__":
    print("="*60)
    print("영화 순위 조회를 위한 브라우저 자동화 도구 설치")
    print("="*60)
    
    choice = input("\n설치할 도구를 선택하세요:\n1. Playwright (권장)\n2. Selenium\n3. 둘 다\n선택 (1/2/3): ")
    
    if choice == "1":
        install_playwright()
    elif choice == "2":
        install_selenium()
    elif choice == "3":
        install_playwright()
        print("\n" + "="*60 + "\n")
        install_selenium()
    else:
        print("잘못된 선택입니다.")