"""
데이터베이스 헬퍼 모듈
DB 연결 및 쿼리 실행 관련 함수들
"""


def get_conn():
    """데이터베이스 연결 (임시 구현)
    
    Returns:
        tuple: (connection, cursor) 또는 (None, None)
    """
    # 실제 DB 연결 구현 필요
    print("⚠️ 데이터베이스 연결이 구현되지 않았습니다.")
    return None, None


def fetch_val(query: str, params: tuple = None):
    """단일 값 조회 (임시 구현)
    
    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
        
    Returns:
        조회된 단일 값 또는 None
    """
    print(f"⚠️ DB 쿼리 실행 필요: {query}")
    return None


def fetch_all(query: str, params: tuple = None):
    """전체 행 조회 (임시 구현)
    
    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
        
    Returns:
        list: 조회된 모든 행
    """
    print(f"⚠️ DB 쿼리 실행 필요: {query}")
    return []


def fetch_one(query: str, params: tuple = None):
    """단일 행 조회 (임시 구현)
    
    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
        
    Returns:
        조회된 단일 행 또는 None
    """
    print(f"⚠️ DB 쿼리 실행 필요: {query}")
    return None


def execute(query: str, params: tuple = None):
    """쿼리 실행 (임시 구현)
    
    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
        
    Returns:
        bool: 실행 성공 여부
    """
    print(f"⚠️ DB 쿼리 실행 필요: {query}")
    return True