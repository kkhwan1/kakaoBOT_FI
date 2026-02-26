"""
차트 생성 유틸리티 모듈
matplotlib 기반 환율/주식 차트 이미지 생성
"""

import os
from io import BytesIO
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend (서버 환경 필수)
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# 한글 폰트 설정 (Windows: Malgun Gothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 공통 색상 팔레트
COLORS = {
    'bg': '#FFFFFF',
    'text': '#1A1A2E',
    'text_secondary': '#6C757D',
    'accent': '#0F3460',
    'bar_colors': ['#E94560', '#0F3460', '#16213E', '#533483'],
    'up': '#E94560',       # 상승 (빨강)
    'down': '#4A90D9',     # 하락 (파랑)
    'flat': '#6C757D',     # 보합 (회색)
    'grid': '#E8E8E8',
    'card_bg': '#F8F9FA',
    'divider': '#DEE2E6',
}

# 통화 라벨 매핑
CURRENCY_LABELS = {
    'USD': '미국 달러 (USD)',
    'EUR': '유럽 유로 (EUR)',
    'JPY': '일본 엔 (JPY)',
    'CNY': '중국 위안 (CNY)',
    'GBP': '영국 파운드 (GBP)',
    'CHF': '스위스 프랑 (CHF)',
    'CAD': '캐나다 달러 (CAD)',
    'AUD': '호주 달러 (AUD)',
}


def _parse_price(price_str: str) -> float:
    """가격 문자열을 float으로 변환한다.

    Args:
        price_str: 콤마가 포함된 가격 문자열 (예: '1,380.50')

    Returns:
        float: 파싱된 숫자 값
    """
    return float(price_str.replace(',', ''))


def create_exchange_chart(exchange_data: dict) -> Figure:
    """환율 데이터를 수평 막대 차트로 생성한다.

    Args:
        exchange_data: 통화별 환율 데이터
            예: {'USD': {'price': '1,380.50'}, 'EUR': {'price': '1,490.20'}, ...}

    Returns:
        Figure: matplotlib Figure 객체
    """
    if not exchange_data:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, '환율 데이터 없음',
                ha='center', va='center', fontsize=16, color=COLORS['text_secondary'])
        ax.set_facecolor(COLORS['bg'])
        fig.patch.set_facecolor(COLORS['bg'])
        ax.axis('off')
        return fig

    # 데이터 준비: 가격 기준 오름차순 정렬 (막대 차트에서 위가 높은 값)
    currencies = list(exchange_data.keys())
    prices = [_parse_price(exchange_data[c]['price']) for c in currencies]
    labels = [CURRENCY_LABELS.get(c, c) for c in currencies]

    sorted_pairs = sorted(zip(labels, prices, currencies), key=lambda x: x[1])
    labels, prices, currencies = zip(*sorted_pairs) if sorted_pairs else ([], [], [])
    labels = list(labels)
    prices = list(prices)

    n = len(labels)
    bar_height = max(0.8, min(1.2, 4.0 / n))
    fig_height = max(3.5, n * 1.3 + 1.5)
    fig, ax = plt.subplots(figsize=(10, fig_height))

    # 막대 색상 할당
    bar_colors = [COLORS['bar_colors'][i % len(COLORS['bar_colors'])] for i in range(n)]

    bars = ax.barh(range(n), prices, height=bar_height, color=bar_colors,
                   edgecolor='white', linewidth=0.5, zorder=3)

    # 막대 위에 가격 표시
    max_price = max(prices) if prices else 1
    for i, (bar, price) in enumerate(zip(bars, prices)):
        price_text = f'{price:,.2f}원'
        # 막대가 충분히 길면 안쪽에, 짧으면 바깥에 표시
        if price > max_price * 0.4:
            ax.text(bar.get_width() - max_price * 0.02, bar.get_y() + bar.get_height() / 2,
                    price_text, ha='right', va='center',
                    fontsize=12, fontweight='bold', color='white', zorder=4)
        else:
            ax.text(bar.get_width() + max_price * 0.01, bar.get_y() + bar.get_height() / 2,
                    price_text, ha='left', va='center',
                    fontsize=12, fontweight='bold', color=COLORS['text'], zorder=4)

    # 축 설정
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels, fontsize=11, fontweight='medium')
    ax.set_xlabel('원 (KRW)', fontsize=10, color=COLORS['text_secondary'])

    # 그리드 및 스타일
    ax.xaxis.grid(True, linestyle='--', alpha=0.3, color=COLORS['grid'], zorder=0)
    ax.yaxis.grid(False)
    ax.set_axisbelow(True)

    # 스파인 제거
    for spine in ['top', 'right', 'bottom']:
        ax.spines[spine].set_visible(False)
    ax.spines['left'].set_color(COLORS['grid'])

    # 제목
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    ax.set_title('실시간 환율 정보', fontsize=16, fontweight='bold',
                 color=COLORS['text'], pad=15, loc='left')
    ax.text(1.0, 1.02, f'기준: {now_str}',
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=9, color=COLORS['text_secondary'])

    # x축 범위 여유
    ax.set_xlim(0, max_price * 1.15)

    # 배경색
    ax.set_facecolor(COLORS['bg'])
    fig.patch.set_facecolor(COLORS['bg'])

    fig.tight_layout(pad=1.5)
    return fig


def create_stock_chart(stock_data: dict) -> Figure:
    """주식 데이터를 정보 카드 스타일로 시각화한다.

    히스토리컬 데이터 없이 현재 스냅샷 정보를 보기 좋게 표현한다.

    Args:
        stock_data: 주식 정보 딕셔너리
            예: {
                'name': '삼성전자', 'code': '005930',
                'current': 72000, 'change': '▲500', 'rate': '+0.70%',
                'open': 71500, 'high': 72500, 'low': 71000,
                'volume': '12,345,678'
            }

    Returns:
        Figure: matplotlib Figure 객체
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    name = stock_data.get('name', '---')
    code = stock_data.get('code', '------')
    current = stock_data.get('current')
    change = stock_data.get('change', '---')
    rate = stock_data.get('rate', '---')
    open_price = stock_data.get('open')
    high_price = stock_data.get('high')
    low_price = stock_data.get('low')
    volume = stock_data.get('volume', '---')

    # 등락 방향 판별 및 색상 선택
    change_str = str(change)
    if '▲' in change_str or '+' in str(rate):
        accent_color = COLORS['up']
        direction_symbol = '▲'
    elif '▼' in change_str or '-' in str(rate):
        accent_color = COLORS['down']
        direction_symbol = '▼'
    else:
        accent_color = COLORS['flat']
        direction_symbol = '─'

    y = 9.2  # 시작 y 좌표

    # --- 종목 헤더 ---
    ax.text(0.5, y, name, fontsize=22, fontweight='bold',
            color=COLORS['text'], va='top')
    ax.text(0.5, y - 0.55, f'({code})', fontsize=11,
            color=COLORS['text_secondary'], va='top')

    y -= 1.5

    # --- 현재가 영역 ---
    # 배경 카드
    from matplotlib.patches import FancyBboxPatch
    card = FancyBboxPatch((0.3, y - 1.8), 9.4, 2.2,
                          boxstyle='round,pad=0.15',
                          facecolor=COLORS['card_bg'],
                          edgecolor=COLORS['divider'], linewidth=1)
    ax.add_patch(card)

    current_text = f'{current:,}원' if current is not None else '---'
    ax.text(5.0, y - 0.2, current_text, fontsize=28, fontweight='bold',
            color=accent_color, ha='center', va='top')

    change_rate_text = f'{change}  ({rate})'
    ax.text(5.0, y - 1.1, change_rate_text, fontsize=14, fontweight='medium',
            color=accent_color, ha='center', va='top')

    y -= 3.0

    # --- 구분선 ---
    ax.plot([0.5, 9.5], [y, y], color=COLORS['divider'], linewidth=1, zorder=2)

    y -= 0.6

    # --- 상세 정보 그리드 (2열) ---
    detail_items = []
    if open_price is not None:
        detail_items.append(('시가', f'{open_price:,}원'))
    if high_price is not None:
        detail_items.append(('고가', f'{high_price:,}원'))
    if low_price is not None:
        detail_items.append(('저가', f'{low_price:,}원'))
    if volume and volume != '---':
        detail_items.append(('거래량', f'{volume}주'))

    col_x = [1.5, 6.0]
    row = 0
    for i, (label, value) in enumerate(detail_items):
        col = i % 2
        row_y = y - (row * 1.0)

        ax.text(col_x[col], row_y, label, fontsize=11,
                color=COLORS['text_secondary'], va='top', fontweight='medium')
        ax.text(col_x[col] + 2.5, row_y, value, fontsize=12,
                color=COLORS['text'], va='top', ha='right', fontweight='bold')

        if col == 1:
            row += 1
    # 마지막 항목이 홀수일 때 row 증가 처리
    if len(detail_items) % 2 == 1:
        row += 1

    # --- 가격 범위 바 (시가/고가/저가가 있을 때) ---
    if all(v is not None for v in [open_price, high_price, low_price]) and high_price > low_price:
        bar_y = y - (row * 1.0) - 0.4

        ax.text(0.5, bar_y, '일중 가격 범위', fontsize=10,
                color=COLORS['text_secondary'], va='top', fontweight='medium')

        bar_y -= 0.55
        bar_left = 1.0
        bar_right = 9.0
        bar_width = bar_right - bar_left
        price_range = high_price - low_price

        # 범위 바 배경
        range_bar = FancyBboxPatch((bar_left, bar_y - 0.15), bar_width, 0.3,
                                   boxstyle='round,pad=0.05',
                                   facecolor=COLORS['grid'],
                                   edgecolor='none')
        ax.add_patch(range_bar)

        # 현재가 위치 표시
        if current is not None and price_range > 0:
            current_pos = bar_left + ((current - low_price) / price_range) * bar_width
            current_pos = max(bar_left, min(bar_right, current_pos))
            ax.plot(current_pos, bar_y, marker='o', markersize=10,
                    color=accent_color, zorder=5)
            ax.plot(current_pos, bar_y, marker='o', markersize=6,
                    color='white', zorder=6)

        # 저가/고가 라벨
        ax.text(bar_left, bar_y - 0.35, f'{low_price:,}',
                fontsize=9, color=COLORS['text_secondary'], ha='left', va='top')
        ax.text(bar_right, bar_y - 0.35, f'{high_price:,}',
                fontsize=9, color=COLORS['text_secondary'], ha='right', va='top')

    # --- 타임스탬프 ---
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    ax.text(9.5, 0.3, f'기준: {now_str}', fontsize=8,
            color=COLORS['text_secondary'], ha='right', va='bottom')

    fig.tight_layout(pad=1.0)
    return fig


def fig_to_bytes(fig: Figure, save_path: str = None) -> bytes:
    """matplotlib Figure를 PNG 바이트로 변환한다.

    Args:
        fig: 변환할 matplotlib Figure 객체
        save_path: 파일 저장 경로 (선택). 지정하면 해당 경로에도 PNG를 저장한다.

    Returns:
        bytes: PNG 이미지 바이트 데이터
    """
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    image_bytes = buf.read()
    buf.close()

    if save_path:
        dir_name = os.path.dirname(save_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(image_bytes)

    plt.close(fig)
    return image_bytes
