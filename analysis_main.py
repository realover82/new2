import streamlit as st
import pandas as pd
from typing import Dict, Any

# 분할된 모듈 임포트
from analysis_utils import check_initial_validity, setup_filtering_ui
from aggregation_logic import aggregate_and_display_summary
from detail_display import display_detail_section
from df_search import display_df_search

def display_analysis_result(analysis_key: str, file_name: str, props: Dict[str, str]):
    """
    세션 상태에 저장된 분석 결과를 Streamlit에 표시하는 메드인 함수입니다.
    """
    
    # 1. 초기 유효성 검사 및 데이터 추출
    validation_result = check_initial_validity(analysis_key, props)
    if validation_result:
        st.error(validation_result)
        return

    summary_data = st.session_state.analysis_data[analysis_key][0]
    all_dates = st.session_state.analysis_data[analysis_key][1]
    df_raw = st.session_state.analysis_results[analysis_key]
    
    st.markdown(f"### '{file_name}' 분석 리포트")
    
    # 2. 필터링 UI 설정 및 필터링된 DF 획득
    # [수정] 반환값에 df_filtered_from_ui 추가
    selected_jig, start_date, end_date, df_filtered_from_ui = setup_filtering_ui(analysis_key, df_raw, all_dates, props)
    
    # === 핵심 수정: UI에서 필터링된 DF를 세션에 저장 및 검증 ===
    df_filtered = df_filtered_from_ui.copy()
    
    # Jig 필터링을 위한 리스트
    jigs_to_display = [selected_jig] if selected_jig != "전체" else sorted(df_raw[props['jig_col']].dropna().unique().tolist())
    
    # 세션 상태에 필터링된 DF 저장
    st.session_state[f'filtered_df_{analysis_key}'] = df_filtered.copy()
    # ======================================
    
    # --- 최종 상태 확인 ---
    if analysis_key == 'Pcb':
        if df_filtered.empty:
            st.error("DEBUG FINAL: 필터링된 DF가 최종적으로 비어있습니다. 테이블/그래프 생성 불가.")
            st.session_state['show_summary_table'] = False 
            return
        else:
            st.success(f"DEBUG FINAL: 필터링된 DF 최종 행 수: {df_filtered.shape[0]} (테이블 생성 가능)")
            
    st.write(f"**분석 시간**: {st.session_state.analysis_time[analysis_key]}")
    st.markdown("---")

    # 3. 데이터 집계 및 기간 요약 테이블 표시 (UI 필터 반영)
    aggregate_and_display_summary(summary_data, all_dates, jigs_to_display, start_date, end_date, analysis_key)

    st.markdown("---")
    
    # 4. 상세 내역 표시
    display_detail_section(analysis_key, df_raw, summary_data, all_dates, jigs_to_display)

    # 5. DF 검색 기능 표시
    display_df_search(analysis_key, df_filtered, props)