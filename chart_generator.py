import pandas as pd
import altair as alt
from typing import Optional
import streamlit as st 

def create_stacked_bar_chart(summary_df: pd.DataFrame, key_prefix: str) -> Optional[alt.Chart]:
    """
    QC 요약 테이블 DataFrame을 사용하여 Altair 누적 막대 그래프를 생성하고 차트 객체를 반환합니다.
    [수정됨]: Altair 레이어링 오류를 해결하고 차트를 안정화했습니다.
    """
    if summary_df.empty:
        st.warning("Chart Debug: 입력 summary_df가 비어있습니다. 차트 생성 불가.")
        return None

    # Altair를 위한 데이터 변환 (Wide to Long)
    df_long = summary_df.melt(
        id_vars=['Date', 'Jig', 'Test'],
        value_vars=['Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)'],
        var_name='Status',
        value_name='Count'
    )
    
    # --- DEBUG 1: 데이터 변환 직후 ---
    st.info(f"Chart Debug 1: Wide to Long 변환 후 데이터 행 수: {df_long.shape[0]}")
    
    # Pass 상태와 0인 값 제거
    df_long = df_long[df_long['Status'] != 'Pass'] 
    df_long = df_long[df_long['Count'] > 0]
    
    # --- DEBUG 2: 필터링 (Pass/0 값 제거) 후 ---
    st.info(f"Chart Debug 2: Pass/0 값 제거 후 최종 데이터 행 수: {df_long.shape[0]}")
    
    if df_long.empty:
        st.error("Chart Debug: 필터링 후 남은 데이터가 0건입니다. 차트 생성 불가.")
        return None 

    # 순서 정의 (Pass 제외)
    status_order = ['미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    color_scale = alt.Scale(
        domain=status_order,
        range=['#FF9800', '#F44336', '#9E9E9E'] 
    )

    # 1. Base 인코딩 정의 (레이어들이 공유할 기본 구조)
    base = alt.Chart(df_long).encode(
        x=alt.X('Test', sort=None, axis=alt.Axis(title='테스트 항목', labelAngle=-45)),
        y=alt.Y('Count', title='유닛 수'),
        color=alt.Color('Status', scale=color_scale, sort=status_order),
        tooltip=['Date', 'Jig', 'Test', 'Status', 'Count']
    ).properties(
        title=f'{key_prefix} 테스트 항목별 불량/제외 결과 (누적 막대 차트)'
    )

    # 2. 막대 (Bar) 레이어 생성
    chart_bar = base.mark_bar()
    
    # 3. 텍스트 (Text) 레이어 생성
    # [핵심 수정]: 텍스트 레이블은 별도의 인코딩을 사용하지 않고, base 인코딩을 오버라이드합니다.
    chart_text = base.mark_text(
        align='center',
        baseline='bottom',
        dy=-5 # 막대 위에 약간 띄우기
    ).encode(
        # Y축을 합계로 설정하여 막대 위에 텍스트를 배치합니다.
        y=alt.Y('sum(Count)', stack='zero', title=''), # Y축 제목 제거
        text=alt.Text('sum(Count)', format=',.0f'),
        color=alt.value('black'), # 텍스트 색상 고정
        # Status 색상 인코딩은 텍스트에서 제거합니다.
        color=alt.value('black'), 
        tooltip=['sum(Count):Q'] # 툴팁은 간략하게
    ).transform_aggregate(
        total_count='sum(Count)',
        groupby=['Test'] # Test 항목별로만 합산합니다.
    )

    # 4. 최종 레이어링 (차트와 텍스트를 합치고 축 설정)
    # [수정] Y축 제목이 겹치지 않도록 차트에서만 Y축 제목을 남기고 텍스트에서는 제거합니다.
    layered_chart = alt.layer(
        chart_bar, 
        chart_text
    ).resolve_scale(
        y='independent'
    ).interactive()
    
    # 5. 합쳐진 레이어에 Date와 Test 항목별 패싯(분할) 적용
    final_chart = layered_chart.facet(
        column=alt.Column('Test', header=alt.Header(titleOrient="bottom", labelOrient="top", title='테스트 항목'))
    )

    return final_chart
