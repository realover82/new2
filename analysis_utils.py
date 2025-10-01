import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

def check_initial_validity(analysis_key: str, props: Dict[str, str]) -> Optional[str]:
    """분석 시작 전 세션 상태의 필수 데이터 존재 여부를 확인합니다."""
    if st.session_state.analysis_results.get(analysis_key) is None:
        return "데이터 로드에 실패했습니다. 파일 형식을 확인해주세요."
    
    if st.session_state.analysis_data.get(analysis_key) is None:
        return "데이터 분석에 실패했습니다. 분석 함수를 확인해주세요."
        
    df_raw = st.session_state.analysis_results[analysis_key]
    all_dates = st.session_state.analysis_data[analysis_key][1]

    if all_dates is None:
        return "데이터 분석에 실패했습니다. 날짜 관련 컬럼 형식을 확인해주세요."
        
    required_columns = [props['jig_col'], props['timestamp_col']]
    missing_columns = [col for col in required_columns if col not in df_raw.columns]
    
    if missing_columns:
        return f"데이터에 필수 컬럼이 없습니다: {', '.join(missing_columns)}. 파일을 다시 확인해주세요."
        
    if df_raw.empty:
        return "원본 데이터가 비어있습니다."
        
    return None

def setup_filtering_ui(analysis_key: str, df_raw: pd.DataFrame, all_dates: List[datetime.date], props: Dict[str, str]) -> Tuple[str, datetime.date, datetime.date]:
    """
    기본 필터링 UI를 설정하고 사용자의 선택을 반환합니다.
    필터링 로직은 이 함수 내에서 데이터를 변경하지 않습니다.
    """
    st.subheader("기본 필터링 (필터링 로직 전체 비활성화)")
    
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        jig_list = sorted(df_raw[props['jig_col']].dropna().unique().tolist()) if props['jig_col'] in df_raw.columns else []
        selected_jig = st.selectbox("PC(Jig) 선택", ["전체"] + jig_list, key=f"jig_select_{analysis_key}") 
    
    min_date = min(all_dates)
    max_date = max(all_dates)

    with filter_col2:
        start_date = st.date_input("시작 날짜", min_value=min_date, max_value=max_date, value=min_date, key=f"start_date_{analysis_key}")
    with filter_col3:
        end_date = st.date_input("종료 날짜", min_value=min_date, max_value=max_date, value=max_date, key=f"end_date_{analysis_key}")

    if start_date > end_date:
        st.error("시작 날짜는 종료 날짜보다 이전이어야 합니다.")
        # 오류 발생 시 기본값 반환
        return selected_jig, min_date, max_date
        
    return selected_jig, start_date, end_date