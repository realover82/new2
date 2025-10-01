import pandas as pd
import altair as alt
from typing import Optional

def create_stacked_bar_chart(summary_df: pd.DataFrame, key_prefix: str) -> Optional[alt.Chart]:
    """
    QC 요약 테이블 DataFrame을 사용하여 Altair 누적 막대 그래프를 생성하고 차트 객체를 반환합니다.
    summary_df는 'Test', 'Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)', 'Date', 'Jig' 컬럼을 포함해야 합니다.
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
    
    # 0인 값은 제거하여 차트를 깔끔하게 만듭니다.
    df_long = df_long[df_long['Status'] != 'Pass'] 
    df_long = df_long[df_long['Count'] > 0]
    
    # # 순서 정의
    # status_order = ['Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    # color_scale = alt.Scale(
    #     domain=status_order,
    #     range=['#4CAF50', '#FF9800', '#F44336', '#9E9E9E']
    # )
    
    # 순서 정의 (Pass 제외)
    status_order = ['미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    color_scale = alt.Scale(
        domain=status_order,
        range=['#FF9800', '#F44336', '#9E9E9E'] # Pass 색상 제외
    )

    base = alt.Chart(df_long).encode(
        x=alt.X('Test', sort=None, axis=alt.Axis(title='테스트 항목', labelAngle=-45)),
        y=alt.Y('Count', title='유닛 수'),
        color=alt.Color('Status', scale=color_scale, sort=status_order),
        tooltip=['Date', 'Jig', 'Test', 'Status', 'Count']
    ).properties(
        title=f'{key_prefix} 테스트 항목별 QC 결과 (누적 막대 차트)'
    )

    chart = base.mark_bar()
    
    # 텍스트 레이블 (차트 위에 값 표시)
    # Altair는 Mark_text를 사용합니다. Stacked bar에서는 레이블을 정확히 중앙에 배치하기 위해 sum(Count)를 사용합니다.
    text = base.mark_text(
        align='center',
        baseline='middle',
        dy=-5 # 막대 위에 약간 띄우기
    ).encode(
        y=alt.Y('sum(Count)', stack='zero'),
        text=alt.Text('sum(Count)', format=',.0f'),
        color=alt.value('black') # 텍스트 색상
    ).transform_aggregate(
        # 각 테스트 항목별로 상위/하위 값을 집계하여 텍스트를 배치합니다.
        total_count='sum(Count)',
        groupby=['Test', 'Status']
    )
    
    # 최종 차트 생성 (레이어를 합침)
    final_chart = (chart).interactive()

    return final_chart
# ```eof

# ---

# ## 2. `streamlit_app.py` 수정 (Jig/Date/차트 로직 통합)

# `generate_dynamic_summary_table` 함수를 수정하여 **테이블 출력 시 Jig와 Date 컬럼을 포함**하고, **차트 버튼 클릭 시 테이블이 사라지지 않도록** 버튼 로직을 수정합니다.

# ```python:Main Streamlit Application:streamlit_app.py
# [Immersive content redacted for brevity.]
# ```eof

# ---

# ## 3. `analysis_main.py` 수정 (Jig/Date 컬럼명 전달)

# `analysis_main.py`에서 `generate_dynamic_summary_table` 호출 시 **테이블 생성에 필요한 컬럼 정보(`props`)**를 추가로 전달하도록 수정합니다.

# ```python:Analysis Main Entry:analysis_main.py
# [Immersive content redacted for brevity.]
# ```eof

# ---

# ## 최종 확인 사항

# # 1.  **3개 파일**을 모두 위 코드로 교체합니다.
# # 2.  **앱을 새로고침**합니다.
# # 3.  **'파일 Pcb 분석'**에서 **날짜나 Jig를 변경**하면, **QC 요약 테이블**에 **Date**와 **Jig**가 표시되며 합산되지 않고 각각의 행으로 분리되어 나타납니다.
# # 4.  **"PCB 요약 차트 보기"** 버튼을 누르면, 테이블 아래에 **동적인 Altair 누적 막대 그래프**가 나타나고, **테이블은 사라지지 않고** 함께 표시됩니다.