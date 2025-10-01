import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# 1. 기능별 분할된 모듈 임포트
from config import ANALYSIS_KEYS, TAB_PROPS_MAP
from analysis_display import display_analysis_result
# 새로 추가된 차트 생성 모듈 임포트
from chart_generator import create_stacked_bar_chart 

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

    # 탭 정의 (총 6개의 탭 생성)
    tab_names = [f"파일 {key} 분석" for key in ANALYSIS_KEYS] + ["PCB QC 요약 그래프"]
    tabs = st.tabs(tab_names)
    
    # === 수정된 부분: 탭 인스턴스를 명시적으로 할당합니다. ===
    
    # 탭 이름 리스트에서 순서대로 탭 인스턴스 추출
    tab_instances = {
        'Pcb': tabs[0],
        'Fw': tabs[1],
        'RfTx': tabs[2],
        'Semi': tabs[3],
        'Batadc': tabs[4],
    }
    chart_tab = tabs[5] # 그래프 탭은 마지막 인덱스 (5)

    # 탭 속성과 분석 함수를 결합한 최종 맵
    tab_map = {
        key: {
            **TAB_PROPS_MAP[key], 
            'tab': tab_instances[key], # 할당된 탭 인스턴스 사용
            'reader': globals()[f"read_csv_with_dynamic_header_for_{key}"] if key != 'Pcb' else read_csv_with_dynamic_header,
            'analyzer': globals()[f"analyze_{key}_data"] if key != 'Pcb' else analyze_data
        }
        for key in ANALYSIS_KEYS
    }
    
    # === 사이드바 컬럼 목록 표시 ===
    st.sidebar.title("현재 데이터 컬럼")
    for key in ANALYSIS_KEYS:
        if key in st.session_state.sidebar_columns and st.session_state.sidebar_columns[key]:
            with st.sidebar.expander(f"**{key.upper()} 컬럼 목록**"):
                st.code(st.session_state.sidebar_columns[key])
    # ====================================================

    # 메인 탭 로직 (CSV 분석 탭)
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
                        # 디버깅을 위해 오류 메시지를 콘솔에도 출력
                        print(f"Error during {key} analysis: {e}") 
                        st.error(f"분석 중 오류 발생: {e}")
                        st.session_state.analysis_results[key] = None

                # 분석 결과가 세션 상태에 저장되어 있으면 표시 함수 호출
                if st.session_state.analysis_results[key] is not None:
                    # analysis_display.py의 함수 호출
                    display_analysis_result(key, st.session_state.uploaded_files[key].name, TAB_PROPS_MAP[key])

    # ==============================
    # 5. 그래프 탭 로직 추가 (분석 데이터 기반으로 변경)
    # ==============================
    with chart_tab:
        st.header("PCB 테스트 항목별 QC 결과 그래프")
        st.markdown("이 그래프는 '파일 Pcb 분석' 탭에서 로드된 실제 분석 데이터를 기반으로 테스트 항목별 QC 결과를 시각화합니다.")
        
        df_pcb = st.session_state.analysis_results.get('Pcb')
        
        # 'PCB QC 요약 그래프 생성' 버튼 표시 조건 확인
        if df_pcb is None or df_pcb.empty:
            st.warning("그래프를 생성하려면 '파일 Pcb 분석' 탭에서 CSV 파일을 로드하고 '분석 실행'을 먼저 완료해야 합니다.")
        else:
            # 이 else 블록이 실행되면 버튼이 나타나야 합니다.
            # 버튼을 눌러 그래프 생성 함수 호출
            if st.button("PCB QC 요약 그래프 생성", key='generate_pcb_chart'): # key 추가
                with st.spinner("그래프 생성 중..."):
                    # 실제 분석된 PCB 데이터(df_pcb)와 키('Pcb')를 차트 생성 함수에 전달
                    chart_figure = create_stacked_bar_chart(df_pcb, 'PCB')
                    
                    if chart_figure:
                        st.pyplot(chart_figure)
                        st.markdown("---")
                        st.success(f"PCB 데이터 ({df_pcb.shape[0]}건)를 기반으로 그래프가 생성되었습니다.")
                    else:
                        st.error("그래프를 생성하는 데 필요한 QC 컬럼을 찾을 수 없거나 데이터가 비어 있습니다. PCB 데이터의 형식을 확인해주세요.")

if __name__ == "__main__":
    main()
