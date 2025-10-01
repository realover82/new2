import pandas as pd
import altair as alt
from typing import Optional

def create_stacked_bar_chart(summary_df: pd.DataFrame, key_prefix: str) -> Optional[alt.Chart]:
    """
    QC 요약 테이블 DataFrame을 사용하여 Altair 누적 막대 그래프를 생성하고 차트 객체를 반환합니다.
    [수정됨]: 'Date'와 'Test' 항목을 X축으로 분리하여 표시합니다.
    """
    if summary_df.empty:
        return None

    # Altair를 위한 데이터 변환 (Wide to Long)
    df_long = summary_df.melt(
        id_vars=['Date', 'Jig', 'Test'],
        value_vars=['Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)'],
        var_name='Status',
        value_name='Count'
    )
    
    # --------------------------
    # Pass 상태와 0인 값 제거
    # --------------------------
    df_long = df_long[df_long['Status'] != 'Pass'] 
    df_long = df_long[df_long['Count'] > 0]
    
    if df_long.empty:
        st.warning("선택된 필터 조건으로는 불량/제외 데이터가 없습니다. 차트를 생성하지 않습니다.")
        return None

    # 순서 정의 (Pass 제외)
    status_order = ['미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    color_scale = alt.Scale(
        domain=status_order,
        range=['#FF9800', '#F44336', '#9E9E9E'] # Pass 색상 제외
    )

    # --------------------------
    # 핵심 수정: X축에 Date와 Test를 결합하여 일별/항목별 분리
    # --------------------------
    base = alt.Chart(df_long).encode(
        # X축을 날짜로 설정하고, 막대를 Test 항목으로 분리합니다.
        x=alt.X('Date', axis=alt.Axis(title='날짜 (일별)', format='%m-%d')),
        y=alt.Y('Count', title='유닛 수'),
        color=alt.Color('Status', scale=color_scale, sort=status_order),
        # Test 항목별로 그래프를 분리 (컬럼 패싯)
        column=alt.Column('Test', header=alt.Header(titleOrient="bottom", labelOrient="top", title='테스트 항목')),
        tooltip=['Date', 'Jig', 'Test', 'Status', 'Count']
    ).properties(
        title=f'{key_prefix} 테스트 항목별 불량/제외 결과 (일별 분리)'
    ).resolve_scale(
        # Y축을 항목별로 독립적으로 설정 (Test 항목이 많을 경우 유용)
        y='independent'
    )

    chart = base.mark_bar()
    
    # 텍스트 레이블 (총합을 막대 위에 표시)
    text = chart.mark_text(
        align='center',
        baseline='bottom',
        dy=-5 # 막대 위에 약간 띄우기
    ).encode(
        y=alt.Y('sum(Count)', stack='zero'),
        text=alt.Text('sum(Count)', format=',.0f'),
        color=alt.value('black') # 텍스트 색상
    )
    
    # 최종 차트 생성 (레이어를 합침)
    final_chart = (chart + text).interactive()

    return final_chart

if __name__ == '__main__':
    # 모듈 테스트용 데이터 (실행하지 않음)
    pass
