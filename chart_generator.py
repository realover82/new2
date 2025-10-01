import pandas as pd
import altair as alt
from typing import Optional

def create_stacked_bar_chart(summary_df: pd.DataFrame, key_prefix: str) -> Optional[alt.Chart]:
    """
    QC 요약 테이블 DataFrame을 사용하여 Altair 누적 막대 그래프를 생성하고 차트 객체를 반환합니다.
    [수정됨]: 'Date'와 'Test' 항목을 X축과 Column으로 분리하여 일별/항목별 통계를 표시합니다.
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

    # 1. Base Chart (패싯 인코딩을 제외한 기본 인코딩만 정의)
    base = alt.Chart(df_long).encode(
        # [핵심 수정]: X축을 Date로 설정하여 날짜별로 막대를 분리
        x=alt.X('Date', axis=alt.Axis(title='날짜 (일별)', format='%m-%d')),
        y=alt.Y('Count', title='유닛 수'),
        color=alt.Color('Status', scale=color_scale, sort=status_order),
        # Jig별로 다른 색상이나 패턴을 원하면 여기에 'Jig'를 추가할 수 있습니다.
        tooltip=['Date', 'Jig', 'Test', 'Status', 'Count']
    ).properties(
        title=f'{key_prefix} 테스트 항목별 불량/제외 결과 (일별 분리)'
    )

    # 2. 막대 (Bar) 레이어 생성
    # X축에 Date를 썼으므로, Date가 중복되지 않도록 Test 항목별로 분리해야 합니다.
    chart_bar = base.mark_bar()
    
    # 3. 텍스트 (Text) 레이어 생성
    chart_text = alt.Chart(df_long).encode(
        # X축을 Date로 설정 (Bar 차트와 동일)
        x=alt.X('Date', sort=None),
        y=alt.Y('sum(Count)', stack='zero'),
        text=alt.Text('sum(Count)', format=',.0f'),
        color=alt.value('black') # 텍스트 색상 고정
    ).mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    )

    # 4. 최종 레이어링 (차트와 텍스트를 합침)
    layered_chart = alt.layer(chart_bar, chart_text).resolve_scale(
        y='independent'
    ).interactive()
    
    # 5. [핵심 수정]: 합쳐진 레이어에 Test 항목별 패싯(분할) 적용
    final_chart = layered_chart.facet(
        column=alt.Column('Test', header=alt.Header(titleOrient="bottom", labelOrient="top", title='테스트 항목'))
    )

    return final_chart
