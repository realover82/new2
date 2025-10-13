import pandas as pd
import altair as alt
from typing import Optional
import streamlit as st 

def create_stacked_bar_chart(summary_df: pd.DataFrame, key_prefix: str) -> Optional[alt.Chart]:
    """
    QC 요약 테이블 DataFrame을 사용하여 Altair 누적 막대 그래프를 생성하고 차트 객체를 반환합니다.
    [수정됨]: 텍스트 레이어의 그룹화(groupby) 기준에 'Date', 'Jig'를 추가하여 렌더링 오류를 해결했습니다.
    """
    if summary_df.empty:
        # st.warning("Chart Debug: 입력 summary_df가 비어있습니다. 차트 생성 불가.")
        return None

    # Altair를 위한 데이터 변환 (Wide to Long)
    df_long = summary_df.melt(
        id_vars=['Date', 'Jig', 'Test'],
        value_vars=['Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)'],
        var_name='Status',
        value_name='Count'
    )
    
    # --- DEBUG 1: 데이터 변환 직후 ---
    # st.info(f"Chart Debug 1: Wide to Long 변환 후 데이터 행 수: {df_long.shape[0]}")
    
    # Pass 상태와 0인 값 제거
    df_long = df_long[df_long['Status'] != 'Pass'] 
    df_long = df_long[df_long['Count'] > 0]
    
    # --- DEBUG 2: 필터링 (Pass/0 값 제거) 후 ---
    # st.info(f"Chart Debug 2: Pass/0 값 제거 후 최종 데이터 행 수: {df_long.shape[0]}")
    
    if df_long.empty:
        # st.error("Chart Debug: 필터링 후 남은 데이터가 0건입니다. 차트 생성 불가.")
        return None 

    # 순서 정의 (Pass 제외)
    status_order = ['미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    color_scale = alt.Scale(
        domain=status_order,
        range=['#FF9800', '#F44336', '#9E9E9E'] 
    )

    # # 1. Base 인코딩 정의 (레이어들이 공유할 기본 구조)
    # base = alt.Chart(df_long).encode(
    #     x=alt.X('Test', sort=None, axis=alt.Axis(title='테스트 항목', labelAngle=-45)),
    #     y=alt.Y('Count', title='유닛 수'),
    #     color=alt.Color('Status', scale=color_scale, sort=status_order),
    #     tooltip=['Date', 'Jig', 'Test', 'Status', 'Count']
    # ).properties(
    #     title=f'{key_prefix} 테스트 항목별 불량/제외 결과 (누적 막대 차트)'
    # )

    # 1. Base 인코딩 정의 (Facet 제거)
    base = alt.Chart(df_long).encode(
        # [핵심 수정]: X축을 Test 항목으로 설정하고, Jig와 Date는 합산됩니다.
        x=alt.X('Test', sort=None, axis=alt.Axis(title='테스트 항목', labelAngle=-45)),
        y=alt.Y('sum(Count)', title='총 불량/제외 건수'), # Y축은 Count의 합산
        color=alt.Color('Status', scale=color_scale, sort=status_order),
        tooltip=[
            'Test', 
            'Status', 
            alt.Tooltip('sum(Count)', format=',.0f', title='합산 건수') # 툴팁에 합산 건수 표시
        ]
        # tooltip=['Date', 'Jig', 'Test', 'Status', 'Count']
    ).properties(
        title=f'{key_prefix} 테스트 항목별 불량/제외 결과 (기간/Jig 합산)'
    )

    # 2. 막대 (Bar) 레이어 생성
    chart_bar = base.mark_bar().interactive()
    # [수정]: Date와 Jig를 구분하는 그룹 인코딩을 X축에 추가합니다.
    # chart_bar = base.mark_bar().encode(
    #     # Test 항목 내에서 Date와 Jig를 그룹으로 묶어 막대를 분리합니다.
    #     x=alt.X('Test:N', axis=alt.Axis(title='Test 항목')),
    #     column=alt.Column('Date', header=alt.Header(title='날짜'), format='%m-%d'), # 날짜별로 컬럼 분리
    #     # color=alt.Color('Jig:N', scale=alt.Scale(range=['#36A2EB', '#FF6384'])) # Jig별 색상 추가 가능
    # ).resolve_scale(
    #     x='independent' # Test 항목별 X축 독립
    # )
    
    # # # 3. 텍스트 (Text) 레이어 생성
    # chart_text = alt.Chart(df_long).encode(
    #     # X축을 Test로 설정 (Bar 차트와 동일)
    #     x=alt.X('Test', sort=None),
    #     y=alt.Y('sum(Count)', stack='zero', title=''), # Y축 제목 제거
    #     text=alt.Text('sum(Count)', format=',.0f'),
    #     color=alt.value('black') # 텍스트 색상을 직접 지정하여 충돌 방지
    # ).mark_text(
    #     align='center',
    #     baseline='bottom',
    #     dy=-5
    # ).transform_aggregate(
    #     total_count='sum(Count)',
    #     # [핵심 수정]: 텍스트 합산 시 Date와 Jig도 그룹핑하여 막대 차트의 그룹 구조를 유지합니다.
    #     # groupby=['Test', 'Date', 'Jig'] 
    #     groupby=['Date', 'Jig', 'Test']
    # )

    # # 3. 텍스트 (Text) 레이어 생성 (막대 위에 값 표시)
    # chart_text = base.mark_text(
    #     align='center',
    #     baseline='middle', # 텍스트를 막대 중간에 배치
    # ).encode(
    #     y=alt.Y('sum(Count)', stack='zero', title=''), 
    #     text=alt.Text('sum(Count)', format=',.0f'),
    #     color=alt.value('white') 
    # )

    # # 3. 텍스트 (Text) 레이어 생성
    # # [핵심 수정]: transform_aggregate 로직을 제거하고, Base 차트와 동일한 그룹화 인코딩을 사용합니다.
    # chart_text = base.mark_text(
    #     align='center',
    #     baseline='middle', # 중앙에 배치하여 막대 안쪽으로 들어가도록 수정
    #     dy=0
    # ).encode(
    #     # Y축을 sum(Count)로 설정하여 막대 안에 텍스트를 배치합니다.
    #     y=alt.Y('sum(Count)', stack='zero', title=''), 
    #     text=alt.Text('Count', format=',.0f'), # 개별 Count 값 표시
    #     color=alt.value('white') # 텍스트 색상 고정
    # )

    # --- DEBUG 3: 최종 차트 레이어링 ---
    # st.success("Chart Debug 3: 최종 레이어링 및 패싯 적용 시작.")
    
    # # 4. 최종 레이어링 (차트와 텍스트를 합치고 축 설정)
    # layered_chart = alt.layer(
    #     chart_bar,
    #     chart_text
    # ).resolve_scale(
    #     y='independent'
    # ).interactive()
    
    # # 5. 합쳐진 레이어에 Test 항목별 
    

    # 4. 최종 차트 반환 (텍스트 레이어 없이 막대 그래프만 사용)
    # [수정] layered_chart 대신 chart_bar에 직접 Facet을 적용할 수 있도록 로직 단순화
    
    # 차트와 텍스트 레이어링을 분리하고, 막대 차트에 패싯을 바로 적용합니다.
    # final_chart = chart_bar.interactive() 

    # # 5. 합쳐진 레이어에 Test 항목별 패싯(분할) 적용
    # final_chart = layered_chart.facet(
    #     # [핵심 수정]: alt.Column()에 format 인수를 사용하지 않음.
    #     #            Facet의 목적은 분할이므로, 인코딩에 Date와 Jig를 모두 포함시킵니다.
    #     column=alt.Column(
    #         'Test', 
    #         header=alt.Header(titleOrient="bottom", labelOrient="top", title='테스트 항목')
    #     ),
    #     row=alt.Row(
    #          'Date', 
    #          header=alt.Header(title='날짜')
    #     )
    #     # Jig별로 나누려면 Test 대신 Jig를 Column으로 사용해야 함.
    #     # 현재는 Test 기준으로 나눕니다.
    # )

     # [수정]: final_chart는 이제 단순 막대 그래프입니다.
    final_chart = chart_bar 

    return final_chart
