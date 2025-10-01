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
        # st.warning은 streamlit_app에서 처리해야 하므로 주석 처리
        # st.warning("선택된 필터 조건으로는 불량/제외 데이터가 없습니다. 차트를 생성하지 않습니다.")
        return None

    # 순서 정의 (Pass 제외)
    status_order = ['미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    color_scale = alt.Scale(
        domain=status_order,
        range=['#FF9800', '#F44336', '#9E9E9E'] # Pass 색상 제외
    )

    # --------------------------
    # 베이스 차트 정의 (패싯 인코딩을 제외한 기본 인코딩만 정의)
    # --------------------------
    base = alt.Chart(df_long).encode(
        x=alt.X('Date', axis=alt.Axis(title='날짜 (일별)', format='%m-%d')),
        y=alt.Y('Count', title='유닛 수'),
        color=alt.Color('Status', scale=color_scale, sort=status_order),
        tooltip=['Date', 'Jig', 'Test', 'Status', 'Count']
    ).properties(
        title=f'{key_prefix} 테스트 항목별 불량/제외 결과 (일별 분리)'
    )

    # 1. 막대 차트 생성 (패싯 제외)
    chart = base.mark_bar()
    
    # 2. 텍스트 레이블 (총합을 막대 위에 표시)
    # 텍스트 레이블을 막대 차트와 독립적으로 생성
    text_layer = chart.mark_text(
        align='center',
        baseline='bottom',
        dy=-5 
    ).encode(
        y=alt.Y('sum(Count)', stack='zero'),
        text=alt.Text('sum(Count)', format=',.0f'),
        color=alt.value('black') 
    ).transform_aggregate(
        total_count='sum(Count)',
        groupby=['Date', 'Jig', 'Test'] # Date, Jig, Test 기준으로 총합 계산
    ).encode(
        # 텍스트 레이어는 색상 인코딩을 Status 대신 검은색으로 고정
        color=alt.value('black') 
    )

    # 3. 레이어링 및 패싯 적용
    # [핵심 수정]: 먼저 막대와 텍스트를 레이어링(합침)
    layered_chart = alt.layer(chart, text_layer).resolve_scale(
        y='independent' # Y축 독립 설정은 레이어링된 차트에 적용
    )
    
    # 그 다음, 합쳐진 레이어에 패싯(Column) 적용
    final_chart = layered_chart.facet(
        column=alt.Column('Test', header=alt.Header(titleOrient="bottom", labelOrient="top", title='테스트 항목'))
    ).interactive()


    return final_chart

if __name__ == '__main__':
    # 모듈 테스트용 데이터 (실행하지 않음)
    pass
