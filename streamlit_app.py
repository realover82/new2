import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# 1. 기능별 분할된 모듈 임포트
from config import ANALYSIS_KEYS, TAB_PROPS_MAP
from analysis_display import display_analysis_result

# 2. 각 CSV 분석 모듈 임포트 (기존 코드 유지)
# 이 파일들은 실제 데이터 로딩 및 분석 로직을 담고 있다고 가정합니다.
from csv2 import read_csv_with_dynamic_header, analyze_data
from csv_Fw import read_csv_with_dynamic_header_for_Fw, analyze_Fw_data
from csv_RfTx import read_csv_with_dynamic_header_for_RfTx, analyze_RfTx_data
from csv_Semi import read_csv_with_dynamic_header_for_Semi, analyze_Semi_data
from csv_Batadc import read_csv_with_dynamic_header_for_Batadc, analyze_Batadc_data

# ==============================
# 메인 실행 함수
# ==============================
def main():
    st.set_page_config(layout="wide")
    st.title("리모컨 생산 데이터 분석 툴")
    st.markdown("---")

    # 세션 상태 초기화
    for state_key in ['analysis_results', 'uploaded_files', 'analysis_data', 'analysis_time']:
        if state_key not in st.session_state:
            st.session_state[state_key] = {k: None for k in ANALYSIS_KEYS}
            
    if 'field_mapping' not in st.session_state:
        st.session_state.field_mapping = {}
    if 'sidebar_columns' not in st.session_state:
        st.session_state.sidebar_columns = {}
        
    # === 상세 내역 필터링을 위한 세션 상태 초기화 ===
    for key in ANALYSIS_KEYS:
        if f'qc_filter_mode_{key}' not in st.session_state:
            st.session_state[f'qc_filter_mode_{key}'] = 'None'
    # ======================================================== 

    # 탭 정의
    tabs = st.tabs([f"파일 {key} 분석" for key in ANALYSIS_KEYS])
    
    # 탭 속성과 분석 함수를 결합한 최종 맵
    tab_map = {
        'Pcb': {**TAB_PROPS_MAP['Pcb'], 'tab': tabs[0], 'reader': read_csv_with_dynamic_header, 'analyzer': analyze_data},
        'Fw': {**TAB_PROPS_MAP['Fw'], 'tab': tabs[1], 'reader': read_csv_with_dynamic_header_for_Fw, 'analyzer': analyze_Fw_data},
        'RfTx': {**TAB_PROPS_MAP['RfTx'], 'tab': tabs[2], 'reader': read_csv_with_dynamic_header_for_RfTx, 'analyzer': analyze_RfTx_data},
        'Semi': {**TAB_PROPS_MAP['Semi'], 'tab': tabs[3], 'reader': read_csv_with_dynamic_header_for_Semi, 'analyzer': analyze_Semi_data},
        'Batadc': {**TAB_PROPS_MAP['Batadc'], 'tab': tabs[4], 'reader': read_csv_with_dynamic_header_for_Batadc, 'analyzer': analyze_Batadc_data}
    }

    # === 사이드바 컬럼 목록 표시 ===
    st.sidebar.title("현재 데이터 컬럼")
    for key in ANALYSIS_KEYS:
        if key in st.session_state.sidebar_columns and st.session_state.sidebar_columns[key]:
            with st.sidebar.expander(f"**{key.upper()} 컬럼 목록**"):
                st.code(st.session_state.sidebar_columns[key])
    # ====================================================

    # 메인 탭 로직
    for key, props in tab_map.items():
        with props['tab']:
            st.header(f"{key.upper()} 데이터 분석")
            st.session_state.uploaded_files[key] = st.file_uploader(f"{key.upper()} 파일을 선택하세요", type=["csv"], key=f"uploader_{key}")
            
            if st.session_state.uploaded_files[key]:
                if st.button(f"{key.upper()} 분석 실행", key=f"analyze_{key}"):
                    try:
                        # 1. 데이터 로드 (reader 함수 호출)
                        df = props['reader'](st.session_state.uploaded_files[key])
                        
                        if df is None or df.empty:
                            st.error(f"{key.upper()} 데이터 파일을 읽을 수 없거나 내용이 비어 있습니다. 파일 형식을 확인해주세요.")
                            st.session_state.analysis_results[key] = None
                            continue
                        
                        # 필수 컬럼 존재 여부 확인
                        if props['jig_col'] not in df.columns or props['timestamp_col'] not in df.columns:
                            st.error(f"데이터에 필수 컬럼 ('{props['jig_col']}', '{props['timestamp_col']}')이 없습니다. 파일을 다시 확인해주세요.")
                            st.session_state.analysis_results[key] = None
                            continue

                        with st.spinner("데이터 분석 및 저장 중..."):
                            
                            # 2. 분석 함수 실행: df에 QC 컬럼이 추가되고, 요약 데이터 및 날짜 정보 반환
                            summary_data, all_dates = props['analyzer'](df)
                            st.session_state.analysis_data[key] = (summary_data, all_dates)
                            
                            # 3. QC 컬럼이 추가된 최종 df를 세션 상태에 저장
                            st.session_state.analysis_results[key] = df.copy() 
                            
                            st.session_state.analysis_time[key] = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # 시간 포함하여 저장
                            
                            # 4. 사이드바/상세 내역을 위한 최종 컬럼 목록 업데이트
                            final_df = st.session_state.analysis_results[key]
                            final_cols = final_df.columns.tolist()
                            st.session_state.sidebar_columns[key] = final_cols
                            st.session_state.field_mapping[key] = final_cols

                        st.success("분석 완료! 결과가 저장되었습니다.")
                        
                    except Exception as e:
                        st.error(f"분석 중 오류 발생: {e}")
                        st.session_state.analysis_results[key] = None

                # 분석 결과가 세션 상태에 저장되어 있으면 표시 함수 호출
                if st.session_state.analysis_results[key] is not None:
                    # analysis_display.py의 함수 호출
                    display_analysis_result(key, st.session_state.uploaded_files[key].name, TAB_PROPS_MAP[key])

if __name__ == "__main__":
    main()
