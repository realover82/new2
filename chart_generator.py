import pandas as pd
import altair as alt
from typing import Optional

def create_stacked_bar_chart(summary_df: pd.DataFrame, key_prefix: str) -> Optional[alt.Chart]:
    """
    QC 요약 테이블 DataFrame을 사용하여 Altair 누적 막대 그래프를 생성하고 차트 객체를 반환합니다.
    [수정됨]: 레이어링 오류 수정 및 안정화. X축은 Test 항목으로 사용.
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
        # 데이터가 없으면 차트 생성 실패
        return None 

    # 순서 정의 (Pass 제외)
    status_order = ['미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    color_scale = alt.Scale(
        domain=status_order,
        range=['#FF9800', '#F44336', '#9E9E9E'] 
    )

    # 1. Base Chart (X, Y, Color 인코딩)
    base = alt.Chart(df_long).encode(
        # X축에 Test 항목 사용 (Jig/Date 필터가 이미 적용된 상태)
        x=alt.X('Test', sort=None, axis=alt.Axis(title='테스트 항목', labelAngle=-45)),
        y=alt.Y('Count', title='유닛 수'),
        color=alt.Color('Status', scale=color_scale, sort=status_order),
        tooltip=['Date', 'Jig', 'Test', 'Status', 'Count']
    ).properties(
        title=f'{key_prefix} 테스트 항목별 불량/제외 결과 (누적 막대 차트)'
    )

    # 2. 막대 (Bar) 레이어
    chart_bar = base.mark_bar()
    
    # 3. 텍스트 (Text) 레이어 (합산 값 표시)
    chart_text = base.mark_text(
        align='center',
        baseline='middle'
    ).encode(
        y=alt.Y('sum(Count)', stack='zero'),
        text=alt.Text('sum(Count)', format=',.0f'),
        color=alt.value('white') # 텍스트 색상을 흰색으로 고정
    ).transform_aggregate(
        # Date와 Jig 필터가 이미 적용되었으므로 Test 항목별로만 합산
        total_count='sum(Count)',
        groupby=['Test', 'Status'] 
    )
    
    # 4. 최종 레이어링 (차트와 텍스트를 합침)
    final_chart = alt.layer(chart_bar, chart_text).interactive()

    return final_chart
# ```eof

# ### 적용 후 재확인

# 1.  **`chart_generator.py`** 파일을 **위의 코드로 교체**합니다.
# 2.  **앱을 새로고침**합니다.
# 3.  **"PCB 요약 차트 보기"** 버튼을 다시 클릭하여 차트가 **테이블 아래**에 표시되는지 확인해 주세요.