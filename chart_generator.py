import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, List
import matplotlib.font_manager as fm

# ==================================
# 1. 한글 폰트 설정 (Streamlit/Matplotlib)
# ==================================
# 폰트 설정 (이 부분이 한글 깨짐을 해결합니다.)
try:
    # 윈도우 환경: 'Malgun Gothic'
    plt.rcParams['font.family'] = 'Malgun Gothic'
except:
    try:
        # 리눅스 환경: 나눔고딕 (설치되어 있어야 함)
        plt.rcParams['font.family'] = 'NanumGothic'
    except:
        pass 
plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지


def create_stacked_bar_chart(summary_df: pd.DataFrame, key_prefix: str) -> Optional[plt.Figure]:
    """
    QC 요약 테이블 DataFrame을 사용하여 테스트 항목별 누적 막대 그래프를 생성하고 Figure 객체를 반환합니다.
    summary_df는 'Test', 'Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)' 컬럼을 포함해야 합니다.
    """
    try:
        # 1. 플롯을 위한 데이터 준비: 필요한 컬럼만 선택
        plot_data_stacked = summary_df[[
            'Pass', 
            '미달 (Under)', 
            '초과 (Over)', 
            '제외 (Excluded)'
        ]]
        
        # 'Test' 컬럼을 인덱스로 설정
        plot_data_stacked.index = summary_df['Test']

        # 2. 누적 막대 차트 생성
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # 누적 막대 차트 생성 (stacked=True)
        plot_data_stacked.plot(
            kind='bar', 
            stacked=True, 
            # 색상: Pass(녹색), 미달(주황), 초과(빨강), 제외(회색)
            color=['#4CAF50', '#FF9800', '#F44336', '#9E9E9E'], 
            ax=ax
        )

        ax.set_title(f'{key_prefix} 테스트 항목별 QC 결과 (누적 막대 차트)', fontsize=16)
        ax.set_xlabel('테스트 항목', fontsize=14)
        ax.set_ylabel('유닛 수', fontsize=14)
        ax.legend(title='결과', loc='upper right')
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.grid(axis='y', linestyle='--')
        
        # 3. 막대 위에 값(숫자) 표시 로직
        for container in ax.containers:
            # 막대별로 레이블 추가
            labels = [f'{v.get_height():.0f}' if v.get_height() > 0 else '' for v in container]
            ax.bar_label(container, labels=labels, label_type='center', fontsize=9)
            
        plt.tight_layout()
        
        return fig
    
    except Exception as e:
        # 오류 발생 시 None을 반환
        return None

if __name__ == '__main__':
    # 모듈 테스트용 데이터 (실행하지 않음)
    pass
