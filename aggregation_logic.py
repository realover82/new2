import streamlit as st
import pandas as pd
from datetime import date, datetime
from typing import Dict, Any, List

def aggregate_and_display_summary(summary_data: Dict, all_dates: List[datetime.date], jigs_to_display: List[str], start_date: date, end_date: date, analysis_key: str, df_filtered: pd.DataFrame):
    """
    주어진 필터 조건(날짜 및 Jig)에 따라 데이터를 집계하고 기간 요약 테이블을 표시합니다.
    df_filtered: analysis_utils에서 날짜/Jig 필터링을 거친 실제 데이터프레임.
    """
    
    # df_filtered에서 실제 집계에 사용될 날짜 목록을 추출합니다. (날짜/Jig 필터가 적용된 결과)
    if df_filtered.empty:
        filtered_dates_ui = []
    else:
        # 필터링된 DF의 timestamp 컬럼을 date 객체로 변환하여 유니크한 날짜 목록을 얻습니다.
        try:
            # df_filtered에는 '__DATE_TEMP__' 컬럼이 없으므로, 원본 컬럼명 사용 또는 유연하게 접근 필요
            # 여기서는 analysis_utils.py에서 사용한 임시 컬럼이 제거되었다고 가정하고, 원본 컬럼명을 사용합니다.
            timestamp_col = st.session_state.field_mapping.get(analysis_key)[1] if st.session_state.field_mapping.get(analysis_key) else all_dates[0] 
            
            # df_filtered에는 이미 날짜 필터가 적용되어 있지만, 여기서는 집계를 위해
            # 필터링된 데이터의 유효한 날짜만 추출합니다.
            temp_dates = pd.to_datetime(df_filtered[timestamp_col], errors='coerce').dt.date
            filtered_dates_ui = sorted(temp_dates.dropna().unique().tolist())
            
        except Exception:
            # 날짜 컬럼을 찾지 못하거나 변환에 실패하면, UI에서 선택된 날짜 범위만 사용 (데이터 0건이 될 가능성 높음)
            filtered_dates_ui = [d for d in all_dates if start_date <= d <= end_date]
            st.warning("경고: 기간 요약 테이블 날짜 추출에 실패하여 UI 날짜 범위로 대체합니다.")


    daily_aggregated_data = {}
    
    # === 집계 로직: UI 필터 범위 내의 실제 날짜만 사용 ===
    for date_obj in filtered_dates_ui: 
        daily_totals = {key: 0 for key in ['total_test', 'pass', 'false_defect', 'true_defect', 'fail']}
        for jig in jigs_to_display:
            # summary_data는 전체 데이터를 기준으로 미리 계산되어 있습니다.
            # 여기서 필터링된 날짜와 Jig에 해당하는 값만 합산해야 합니다.
            data_point = summary_data.get(jig, {}).get(date_obj.strftime('%Y-%m-%d'))
            if data_point:
                for key in daily_totals:
                    daily_totals[key] += data_point.get(key, 0)
        daily_aggregated_data[date_obj] = daily_totals

    # 기간 요약 테이블의 '총 테스트 수'가 df_filtered의 행 수와 일치하도록 조정합니다.
    # df_filtered는 이미 날짜와 Jig 필터가 적용된 상태입니다.
    # summary_data는 '가성불량', '진성불량' 등 세부 카테고리를 포함합니다.
    
    # --- 요약 (날짜 범위 요약 테이블) ---
    st.subheader("기간 요약")
    
    if filtered_dates_ui:
        summary_df_data = {
            '날짜': [d.strftime('%m-%d') for d in filtered_dates_ui],
            '총 테스트 수': [daily_aggregated_data.get(d, {}).get('total_test', 0) for d in filtered_dates_ui],
            'PASS': [daily_aggregated_data.get(d, {}).get('pass', 0) for d in filtered_dates_ui],
            '가성불량': [daily_aggregated_data.get(d, {}).get('false_defect', 0) for d in filtered_dates_ui],
            '진성불량': [daily_aggregated_data.get(d, {}).get('true_defect', 0) for d in filtered_dates_ui],
            'FAIL': [daily_aggregated_data.get(d, {}).get('fail', 0) for d in filtered_dates_ui]
        }
        summary_df = pd.DataFrame(summary_df_data).set_index('날짜')
        st.dataframe(summary_df.transpose())
    else:
        st.info("선택된 UI 날짜 조건에 해당하는 요약 데이터가 없습니다.")

    # 이 시점에서 filtered_dates_ui를 저장하여 detail_display에서 사용
    st.session_state[f'agg_dates_{analysis_key}'] = filtered_dates_ui