import pandas as pd
import altair as alt
from typing import Optional

def create_stacked_bar_chart(summary_df: pd.DataFrame, key_prefix: str) -> Optional[alt.Chart]:
    """
    QC 요약 테이블 DataFrame을 사용하여 Altair 누적 막대 그래프를 생성하고 차트 객체를 반환합니다.
    [수정됨]: X축을 'Date'로 설정하고, 'Test' 항목별로 그래프를 분리(Facet)하여 일별/항목별 통계를 표시합니다.
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
    
    # Pass 상태와 0인 값 제거
    df_long = df_long[df_long['Status'] != 'Pass'] 
    df_long = df_long[df_long['Count'] > 0]
    
    if df_long.empty:
        return None 

    # 순서 정의 (Pass 제외)
    status_order = ['미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    color_scale = alt.Scale(
        domain=status_order,
        range=['#FF9800', '#F44336', '#9E9E9E'] 
    )

    # --------------------------
    # 핵심 수정: 인코딩 및 패싯 변경
    # --------------------------
    # X축: Date (일별 분리)
    # Column: Test (항목별 분리)
    
    base = alt.Chart(df_long).encode(
        # X축을 날짜로 설정하고 Test 항목 내에서 그룹을 분리합니다.
        x=alt.X('Date', axis=alt.Axis(title='날짜', format='%m-%d')),
        y=alt.Y('Count', title='유닛 수'),
        color=alt.Color('Status', scale=color_scale, sort=status_order),
        # tooltip에 Date, Jig, Test 모두 포함
        tooltip=['Date', 'Jig', 'Test', 'Status', 'Count']
    ).properties(
        title=f'{key_prefix} 테스트 항목별 불량/제외 결과 (일별 분리)'
    ).resolve_scale(
        y='independent' # Y축 독립 설정
    )

    # 2. 막대 (Bar) 레이어: Date와 Test 항목별로 막대를 그립니다.
    chart_bar = base.mark_bar()
    
    # 3. 텍스트 (Text) 레이어
    chart_text = chart_bar.mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        y=alt.Y('sum(Count)', stack='zero'),
        text=alt.Text('sum(Count)', format=',.0f'),
        color=alt.value('black') 
    ).transform_aggregate(
        total_count='sum(Count)',
        # Date, Jig, Test별로 합산합니다.
        groupby=['Date', 'Jig', 'Test', 'Status'] 
    ).encode(
        color=alt.value('black') 
    )

    # 4. 최종 레이어링 및 패싯 적용: Test 항목별로 그래프를 분리합니다.
    layered_chart = alt.layer(chart_bar, chart_text).resolve_scale(
        y='independent'
    )
    
    final_chart = layered_chart.facet(
        column=alt.Column('Test', header=alt.Header(titleOrient="bottom", labelOrient="top", title='테스트 항목'))
    ).interactive()


    return final_chart
