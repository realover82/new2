import streamlit as st
import pandas as pd
from datetime import date, datetime
from typing import Dict, Any, List

def aggregate_and_display_summary(summary_data: Dict, all_dates: List[datetime.date], jigs_to_display: List[str], start_date: date, end_date: date, analysis_key: str):
    """
    주어진 필터 조건에 따라 데이터를 집계하고 기간 요약 테이블을 표시합니다.
    """
    
    # UI 필터 범위 내의 날짜만 사용
    filtered_dates_ui = [d for d in all_dates if start_date <= d <= end_date] 
    
    daily_aggregated_data = {}
    
    # === 집계 로직: UI 필터 범위 내에서 Jig별로 집계 ===
    for date_obj in filtered_dates_ui: 
        daily_totals = {key: 0 for key in ['total_test', 'pass', 'false_defect', 'true_defect', 'fail']}
        for jig in jigs_to_display:
            # summary_data에서 해당 Jig와 날짜의 데이터 포인트 추출
            data_point = summary_data.get(jig, {}).get(date_obj.strftime('%Y-%m-%d'))
            if data_point:
                for key in daily_totals:
                    daily_totals[key] += data_point.get(key, 0)
        daily_aggregated_data[date_obj] = daily_totals

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

    # 이 시점에서 filtered_dates_ui를 다시 저장하여 detail_display에서 사용 (optional)
    st.session_state[f'agg_dates_{analysis_key}'] = filtered_dates_ui