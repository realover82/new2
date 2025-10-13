import pandas as pd #Add new feature for user authentication
# import altair as alt
from typing import Optional
import streamlit as st 

# def create_stacked_bar_chart(summary_df: pd.DataFrame, key_prefix: str) -> Optional[alt.Chart]:
def create_simple_bar_chart(df: pd.DataFrame, key_prefix: str, jig_separated: bool):
        
    """
    QC 요약 테이블 DataFrame을 사용하여 Altair 누적 막대 그래프를 생성하고 차트 객체를 반환합니다.
    [수정됨]: 텍스트 레이어의 그룹화(groupby) 기준에 'Date', 'Jig'를 추가하여 렌더링 오류를 해결했습니다.
    """
    # if summary_df.empty:
    #     # st.warning("Chart Debug: 입력 summary_df가 비어있습니다. 차트 생성 불가.")
    #     return None
    if df.empty:
        st.error("차트 생성 실패: 입력 데이터가 비어 있습니다.")
        return
    
    # 1. 차트 데이터 준비
    # df_chart_base = df.copy()

    # df_chart_base['Test_ID'] = (
    #         df_chart_base['Date'].astype(str) + " / " + 
    #         df_chart_base['Jig'].astype(str) + " / " + 
    #         df_chart_base['Test']
    #     )
    # x_axis_label = '날짜 / Jig / 테스트 항목'

    # 1. 차트 데이터 준비: 불량 항목만 포함하여 복사
    df_chart_base = df[['미달 (Under)', '초과 (Over)', 'Failure']].copy()
    
    # 2. X축 레이블 생성 및 데이터 그룹화
    if group_by_col == 'Date_Jig_Test':
        # 일별/Jig별/Test 항목별 분리 (가장 상세)
        df_chart_base['X_Axis'] = (
            df['Date'].astype(str) + "/" + df['Jig'].astype(str) + "/" + df['Test']
        )
        x_axis_label = '날짜 / Jig / 테스트 항목'
        df_chart = df_chart_base.set_index('X_Axis')

    elif group_by_col == 'Date':
        # 날짜별 합산
        df_chart_base['X_Axis'] = df['Date'].astype(str)
        df_chart = df_chart_base.groupby('X_Axis')[['미달 (Under)', '초과 (Over)', 'Failure']].sum()
        x_axis_label = '날짜별 합산'
        
    elif group_by_col == 'Jig':
        # Jig별 합산
        df_chart_base['X_Axis'] = df['Jig'].astype(str)
        df_chart = df_chart_base.groupby('X_Axis')[['미달 (Under)', '초과 (Over)', 'Failure']].sum()
        x_axis_label = 'Jig별 합산'

    elif group_by_col == 'Test':
        # Test 항목별 합산
        df_chart_base['X_Axis'] = df['Test'].astype(str)
        df_chart = df_chart_base.groupby('X_Axis')[['미달 (Under)', '초과 (Over)', 'Failure']].sum()
        x_axis_label = '테스트 항목별 합산'
    
    else:
        st.error("잘못된 그룹화 기준입니다.")
        return

    # 3. Streamlit의 기본 막대 차트 위젯을 사용하여 출력
    st.subheader(f"{title_suffix} - {x_axis_label}")
    st.bar_chart(df_chart) 
    st.caption(f"X축: {x_axis_label}")


# [레거시 함수 삭제]: 이전의 create_simple_bar_chart 함수는 새로운 함수로 대체됨
# (create_simple_bar_chart 함수는 이 파일의 맨 위 함수로 정의됨)