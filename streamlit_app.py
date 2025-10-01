import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# 1. 기능별 분할된 모듈 임포트
from config import ANALYSIS_KEYS, TAB_PROPS_MAP
from analysis_display import display_analysis_result
from chart_generator import create_stacked_bar_chart 

# 2. 각 CSV 분석 모듈 임포트 (기존 코드 유지)
from csv2 import read_csv_with_dynamic_header, analyze_data
from csv_Fw import read_csv_with_dynamic_header_for_Fw, analyze_Fw_data
from csv_RfTx import read_csv_with_dynamic_header_for_RfTx, analyze_RfTx_data
from csv_Semi import read_csv_with_dynamic_header_for_Semi, analyze_Semi_data
from csv_Batadc import read_csv_with_dynamic_header_for_Batadc, analyze_Batadc_data

# ==============================
# 콜백 함수 정의
# ==============================
def set_show_chart_true():
    """그래프 표시 플래그를 True로 설정하는 콜백 함수"""
    st.session_state.show_pcb_chart = True
    
def set_show_chart_false():
    """그래프 표시 플래그를 False로 설정하는 콜백 함수"""
    st.session_state.show_pcb_chart = False

# ==============================
# 메인 실행 함수
# ==============================
def main():
    st.set_page_config(layout="wide")
    
    # --------------------------
    # HEADER 영역 시작
    # --------------------------
    st.title("리모컨 생산 데이터 분석 툴 [Header]")
    st.markdown("---")

    # 세션 상태 초기화 (생략)
    for state_key in ['analysis_results', 'uploaded_files', 'analysis_data', 'analysis_time']:
        if state_key not in st.session_state:
            st.session_state[state_key] = {k: None for k in ANALYSIS_KEYS}
            
    if 'field_mapping' not in st.session_state:
        st.session_state.field_mapping = {}
    if 'sidebar_columns' not in st.session_state:
        st.session_state.sidebar_columns = {}
        
    for key in ANALYSIS_KEYS:
        if f'qc_filter_mode_{key}' not in st.session_state:
            st.session_state[f'qc_filter_mode_{key}'] = 'None'
    
    if 'show_pcb_chart' not in st.session_state:
        st.session_state.show_pcb_chart = False
    
    tab_map = {
        key: {
            **TAB_PROPS_MAP[key], 
            'reader': globals()[f"read_csv_with_dynamic_header_for_{key}"] if key != 'Pcb' else read_csv_with_dynamic_header,
            'analyzer': globals()[f"analyze_{key}_data"] if key != 'Pcb' else analyze_data
        }
        for key in ANALYSIS_KEYS
    }
    
    # ====================================================
    # 1. 사이드바: 분석 항목 선택 라디오 버튼 및 설정
    # ====================================================
    st.sidebar.title("분석 항목 선택")
    
    analysis_options = {key: f"파일 {key} 분석" for key in ANALYSIS_KEYS}
    default_key = st.session_state.get('last_selected_analysis_key', 'Pcb')
    
    selected_analysis_label = st.sidebar.radio(
        "분석할 데이터 선택", 
        list(analysis_options.values()),
        index=list(analysis_options.keys()).index(default_key),
        key='analysis_radio'
    )
    
    selected_key = next(key for key, label in analysis_options.items() if label == selected_analysis_label)
    st.session_state.last_selected_analysis_key = selected_key
    
    # 사이드바에 현재 데이터 컬럼 목록 표시
    st.sidebar.markdown("---")
    st.sidebar.subheader("현재 데이터 컬럼")
    if selected_key in st.session_state.sidebar_columns and st.session_state.sidebar_columns[selected_key]:
        st.sidebar.expander(f"**{selected_key.upper()} 컬럼 목록**").code(st.session_state.sidebar_columns[selected_key])
    else:
        st.sidebar.info("분석 실행 후 컬럼 목록이 표시됩니다.")

    # ====================================================
    # 2. 사이드바: PCB QC 요약 그래프 버튼 배치
    # ====================================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("QC 결과 시각화")

    df_pcb = st.session_state.analysis_results.get('Pcb')
    
    if df_pcb is None or df_pcb.empty:
        st.sidebar.warning("'파일 Pcb 분석' 실행 후 그래프 버튼이 나타납니다.")
    else:
        # 버튼 표시 로직
        if st.session_state.show_pcb_chart:
            st.sidebar.button("그래프 숨기기", on_click=set_show_chart_false, key='hide_pcb_chart')
        else:
            st.sidebar.button("PCB QC 요약 그래프 보기", on_click=set_show_chart_true, key='show_pcb_chart_btn')
        
        # 다른 분석 항목을 선택하면 그래프 플래그 초기화
        if selected_key != 'Pcb':
             st.session_state.show_pcb_chart = False
    
    # --------------------------
    # MAIN 영역 시작
    # --------------------------
    st.markdown("---")
    st.markdown("## [Main Content Start]")
    st.markdown("---")
    
    key = selected_key
    props = tab_map[key]
    
    st.header(f"분석 대상: {key.upper()} 데이터 분석")
    
    # --- 그래프 출력 위치 (Main Content 상단) ---
    df_pcb_filtered = st.session_state.get('filtered_df_Pcb')
    
    if st.session_state.show_pcb_chart and df_pcb_filtered is not None and not df_pcb_filtered.empty:
        
        st.markdown("---")
        st.subheader("PCB 테스트 항목별 QC 결과 그래프") 
        
        try:
            with st.container():
                with st.spinner("그래프 생성 중..."):
                    chart_figure = create_stacked_bar_chart(df_pcb_filtered, 'PCB')
                    
                    if chart_figure:
                        st.pyplot(chart_figure)
                        st.info(f"PCB 데이터 (필터링된 {df_pcb_filtered.shape[0]}건)를 기반으로 그래프가 생성되었습니다.")
                    else:
                        st.error("그래프를 생성하는 데 필요한 QC 컬럼을 찾을 수 없거나 데이터가 비어 있습니다.")
        except Exception as e:
            st.error(f"그래프 렌더링 중 오류 발생: {e}")
            st.session_state.show_pcb_chart = False
            
    st.markdown("---") 
    # -----------------------------------------------

    st.session_state.uploaded_files[key] = st.file_uploader(f"{key.upper()} 파일을 선택하세요", type=["csv"], key=f"uploader_{key}")
    
    if st.session_state.uploaded_files[key]:
        if st.button(f"{key.upper()} 분석 실행", key=f"analyze_{key}"):
            try:
                df = props['reader'](st.session_state.uploaded_files[key])
                
                if df is None or df.empty:
                    st.error(f"{key.upper()} 데이터 파일을 읽을 수 없거나 내용이 비어 있습니다. 파일 형식을 확인해주세요.")
                    st.session_state.analysis_results[key] = None
                else:
                    if props['jig_col'] not in df.columns or props['timestamp_col'] not in df.columns:
                        st.error(f"데이터에 필수 컬럼 ('{props['jig_col']}', '{props['timestamp_col']}')이 없습니다. 파일을 다시 확인해주세요.")
                        st.session_state.analysis_results[key] = None
                    else:
                        with st.spinner("데이터 분석 및 저장 중..."):
                            summary_data, all_dates = props['analyzer'](df)
                            st.session_state.analysis_data[key] = (summary_data, all_dates)
                            st.session_state.analysis_results[key] = df.copy() 
                            st.session_state.analysis_time[key] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            final_df = st.session_state.analysis_results[key]
                            final_cols = final_df.columns.tolist()
                            st.session_state.sidebar_columns[key] = final_cols
                            st.session_state.field_mapping[key] = final_cols
                            
                            st.session_state.show_pcb_chart = False 
                            st.success("분석 완료! 결과가 저장되었습니다.")
                        
            except Exception as e:
                print(f"Error during {key} analysis: {e}") 
                st.error(f"분석 중 오류 발생: {e}")
                st.session_state.analysis_results[key] = None

        if st.session_state.analysis_results.get(key) is not None:
            # 상세 분석 결과 (Main Content의 주요 부분)
            display_analysis_result(key, st.session_state.uploaded_files[key].name, TAB_PROPS_MAP[key])
            
    # --------------------------
    # FOOTER 영역 시작 (Main Content의 모든 요소가 끝난 지점)
    # --------------------------
    st.markdown("---")
    st.markdown("## [Footer Content Start]")
    st.markdown("데이터 분석 툴 v1.0 | Google Gemini 기반 분석")
    st.markdown("---")


if __name__ == "__main__":
    main()
