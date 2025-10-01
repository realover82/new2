import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional

# ==================================
# 1. 한글 폰트 설정 (Streamlit 환경에 맞게 간소화)
# ==================================
# 요청하신 대로 폰트 설정을 명시적으로 반영합니다.
# Streamlit 환경에서 'Malgun Gothic' 또는 'NanumGothic'이 설치되어 있어야 합니다.
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지


def create_stacked_bar_chart(df: pd.DataFrame, key_prefix: str) -> Optional[plt.Figure]:
    """
    분석된 DataFrame을 사용하여 테스트 항목별 누적 막대 그래프를 생성하고 Figure 객체를 반환합니다.
    (df에는 이미 "_QC" 컬럼이 추가되어 있어야 합니다.)
    """
    try:
        # 1. QC 컬럼 식별
        # 분석된 DataFrame(df)에서 "_QC"로 끝나는 모든 컬럼을 찾습니다.
        qc_columns = [col for col in df.columns if col.endswith('_QC')]
        
        if not qc_columns:
            # QC 컬럼이 없으면 그래프 생성 불가
            return None 

        # 2. QC 상태를 차트 카테고리로 매핑 (데이터 부족은 '제외'로 처리하여 집계)
        status_map = {
            'Pass': 'Pass',
            '미달': '미달',
            '초과': '초과',
            '제외': '제외',
            '데이터 부족': '제외' 
        }

        # 3. 테스트 항목별로 상태 카운트 집계
        summary_list = []
        for qc_col in qc_columns:
            # 테스트 항목 이름 (예: PcbUsbCurr_QC -> PcbUsbCurr)
            test_name = qc_col.replace('_QC', '')
            
            # 해당 QC 컬럼의 상태별 카운트
            status_counts = df[qc_col].value_counts().to_dict()
            
            row = {'Test': test_name}
            
            # 카테고리 초기화
            for cat in ['Pass', '미달', '초과', '제외']:
                row[cat] = 0

            # 카운트 집계
            for status, count in status_counts.items():
                mapped_status = status_map.get(status, '제외')
                row[mapped_status] += count
                
            summary_list.append(row)

        # 4. 플롯을 위한 DataFrame 준비
        summary_df = pd.DataFrame(summary_list)
        if summary_df.empty:
            return None

        # Set index and select columns for plotting
        plot_data_stacked = summary_df.set_index('Test')[['Pass', '미달', '초과', '제외']]


        # ==================================
        # 5. 누적 막대 차트 생성
        # ==================================
        fig, ax = plt.subplots(figsize=(10, 6))
        
        plot_data_stacked.plot(
            kind='bar', 
            stacked=True, 
            # 색상: Pass(녹색), 미달(주황), 초과(빨강), 제외(회색)
            color=['#4CAF50', '#FF9800', '#F44336', '#9E9E9E'], 
            ax=ax
        )

        ax.set_title(f'{key_prefix} 테스트 항목별 QC 결과 (누적 막대 차트)', fontsize=14)
        ax.set_xlabel('테스트 항목', fontsize=12)
        ax.set_ylabel('유닛 수', fontsize=12)
        ax.legend(title='결과', loc='upper right')
        plt.xticks(rotation=45, ha='right') 
        plt.grid(axis='y', linestyle='--')
        plt.tight_layout()
        
        return fig
    
    except Exception as e:
        # 오류 발생 시 None을 반환
        print(f"Error creating chart: {e}")
        return None

if __name__ == '__main__':
    # 모듈 테스트용 코드: 임의의 테스트 데이터 생성
    test_data = {
        'Test_A_QC': ['Pass', '미달', 'Pass', '초과', '제외', 'Pass', '데이터 부족'],
        'Test_B_QC': ['Pass', 'Pass', 'Pass', 'Pass', '미달', '미달', '초과'],
        'Other_Col': [1, 2, 3, 4, 5, 6, 7]
    }
    test_df = pd.DataFrame(test_data)
    
    fig = create_stacked_bar_chart(test_df, 'TEST_DATA')
    if fig:
        plt.show()
        plt.close(fig)
