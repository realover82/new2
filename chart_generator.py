import pandas as pd
import altair as alt
from typing import Optional

def create_stacked_bar_chart(summary_df: pd.DataFrame, key_prefix: str) -> Optional[alt.Chart]:
    """
    QC 요약 테이블 DataFrame을 사용하여 Altair 누적 막대 그래프를 생성하고 차트 객체를 반환합니다.
    [수정됨]: 'mark' 오류 해결 및 레이어링 로직 안정화.
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
        x=alt.X('Test', sort=None, axis=alt.Axis(title='테스트 항목', labelAngle=-45)),
        y=alt.Y('Count', title='유닛 수'),
        color=alt.Color('Status', scale=color_scale, sort=status_order),
        tooltip=['Date', 'Jig', 'Test', 'Status', 'Count']
    ).properties(
        title=f'{key_prefix} 테스트 항목별 불량/제외 결과 (누적 막대 차트)'
    )

    # 2. 막대 (Bar) 레이어 생성
    chart_bar = base.mark_bar()
    
    # 3. 텍스트 (Text) 레이어 생성 (이 부분이 오류의 원인이었습니다)
    # [수정]: base 차트에서 다시 시작하여 mark_text를 호출합니다.
    chart_text = alt.Chart(df_long).encode(
        # Bar 차트와 동일한 X/Y 인코딩을 사용합니다.
        x=alt.X('Test', sort=None),
        y=alt.Y('sum(Count)', stack='zero'),
        # 텍스트 인코딩을 추가합니다.
        text=alt.Text('sum(Count)', format=',.0f'),
        color=alt.value('black') # 텍스트 색상 고정
    ).mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    )

    # 4. 최종 레이어링 (차트와 텍스트를 합침)
    final_chart = alt.layer(chart_bar, chart_text).resolve_scale(
        y='independent'
    ).interactive()

    return final_chart
