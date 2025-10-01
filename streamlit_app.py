import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# 1. 기능별 분할된 모듈 임포트
from config import ANALYSIS_KEYS, TAB_PROPS_MAP
from analysis_main import display_analysis_result 
# from chart_generator import create_stacked_bar_chart 

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
    """테이블 표시 플래그를 True로 설정하는 콜백 함수"""
    st.session_state.show_summary_table = True
    
def set_show_chart_false():
    """테이블 표시 플래그를 False로 설정하는 콜백 함수"""
    st.session_state.show_summary_table = False

# ==============================
# 동적 요약 테이블 생성 함수 (선택된 _QC 컬럼만 반영)
# ==============================
def generate_dynamic_summary_table(df: pd.DataFrame, selected_fields: list):
    """필터링된 DataFrame과 선택된 필드를 사용하여 테스트 항목별 QC 결과 요약 테이블을 생성합니다."""
    if df.empty:
        st.warning("필터링된 데이터가 없어 요약 테이블을 생성할 수 없습니다.")
        return

    # 1. QC 컬럼 식별: selected_fields 중 '_QC'로 끝나는 유효한 컬럼만 통계에 사용합니다.
    qc_columns = [col for col in selected_fields if col.endswith('_QC') and col in df.columns and df[col].dtype == object]
    
    if not qc_columns:
        st.warning("테이블 생성 불가: '상세 내역'에서 _QC로 끝나는 품질 관리 컬럼을 1개 이상 선택해 주세요.")
        return

    # 2. 상태 매핑: '데이터 부족'은 '제외'로 처리
    status_map = {
        'Pass': 'Pass',
        '미달': '미달 (Under)',
        '초과': '초과 (Over)',
        '제외': '제외 (Excluded)',
        '데이터 부족': '제외 (Excluded)' 
    }
    
    summary_data_list = []
    
    for qc_col in qc_columns:
        test_name = qc_col.replace('_QC', '')
        
        # 상태 카운트 집계
        status_counts = df[qc_col].value_counts().to_dict()
        
        row = {'Test': test_name}
        total_count = 0
        failure_count = 0
        
        result_counts = {
            'Pass': 0, 
            '미달 (Under)': 0, 
            '초과 (Over)': 0, 
            '제외 (Excluded)': 0
        }
        
        for status, count in status_counts.items():
            mapped_status = status_map.get(status)
            if mapped_status:
                result_counts[mapped_status] += count
                total_count += count
                
                # '미달'과 '초과'만 불량(Failure)으로 간주
                if mapped_status in ['미달 (Under)', '초과 (Over)']:
                    failure_count += count
        
        # 행 데이터 생성
        row['Pass'] = result_counts['Pass']
        row['미달 (Under)'] = result_counts['미달 (Under)']
        row['초과 (Over)'] = result_counts['초과 (Over)']
        row['제외 (Excluded)'] = result_counts['제외 (Excluded)']
        row['Total'] = total_count
        row['Failure'] = failure_count
        row['Failure Rate (%)'] = f"{(failure_count / total_count * 100):.1f}%" if total_count > 0 else "0.0%"
        
        summary_data_list.append(row)
        
    # 최종 DataFrame 생성
    summary_df = pd.DataFrame(summary_data_list).set_index('Test')
    
    st.markdown("---")
    st.subheader("PCB 테스트 항목별 QC 결과 요약 테이블 (동적)")
    st.dataframe(summary_df)
    st.markdown("---")

# ==============================
# 메인 실행 함수
# ==============================
def main():
    st.set_page_config(layout="wide")
    
    # --------------------------
    # HEADER 영역 시작 
    # --------------------------
    st.title("리모컨 생산 데이터 분석 툴") 
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
    
    if 'show_summary_table' not in st.session_state:
        st.session_state.show_summary_table = False
    
    tab_map = {
        key: {
            **TAB_PROPS_MAP[key], 
            'reader': globals()[f"read_csv_with_dynamic_header_for_{key}"] if key != 'Pcb' else read_csv_with_dynamic_header,
            'analyzer': globals()[f"analyze_{key}_data"] if key != 'Pcb' else analyze_data
        }
        for key in ANALYSIS_KEYS
    }
    
    # ====================================================
    # 1. 사이드바: 분석 항목 선택 라디오 버튼 및 설정 (생략)
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
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("현재 데이터 컬럼")
    if selected_key in st.session_state.sidebar_columns and st.session_state.sidebar_columns[selected_key]:
        st.sidebar.expander(f"**{selected_key.upper()} 컬럼 목록**").code(st.session_state.sidebar_columns[selected_key])
    else:
        st.sidebar.info("분석 실행 후 컬럼 목록이 표시됩니다.")

    # ====================================================
    # 2. 사이드바: 테이블 표시 버튼 배치 (생략)
    # ====================================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("QC 결과 시각화")

    df_pcb = st.session_state.analysis_results.get('Pcb')
    
    if df_pcb is None or df_pcb.empty:
        st.sidebar.warning("'파일 Pcb 분석' 실행 후 버튼이 나타납니다.")
    else:
        if st.session_state.show_summary_table:
            st.sidebar.button("테이블 숨기기", on_click=set_show_chart_false, key='hide_pcb_table')
        else:
            st.sidebar.button("PCB 요약 테이블 보기", on_click=set_show_chart_true, key='show_pcb_table_btn')
        
        if selected_key != 'Pcb':
             st.session_state.show_summary_table = False
    
    # --------------------------
    # MAIN 영역 2등분 시작
    # --------------------------
    
    # 메인 화면을 분석 섹션 (왼쪽, 2/3)과 테이블 섹션 (오른쪽, 1/3)으로 나눕니다.
    main_col, table_col = st.columns([2, 1]) 
    
    # --- 1. 왼쪽 컬럼 (분석 실행 및 상세 내역) ---
    with main_col:
        
        # st.markdown("## [Main Content Start]") # 주석 처리
        st.markdown("---") 

        key = selected_key
        props = tab_map[key]
        
        st.header(f"분석 대상: {key.upper()} 데이터 분석")
        
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
                                
                                st.session_state.show_summary_table = False 
                                st.success("분석 완료! 결과가 저장되었습니다.")
                            
                except Exception as e:
                    print(f"Error during {key} analysis: {e}") 
                    st.error(f"분석 중 오류 발생: {e}")
                    st.session_state.analysis_results[key] = None

            if st.session_state.analysis_results.get(key) is not None:
                # 상세 분석 결과 (기간 요약, 상세 내역 등)
                display_analysis_result(key, st.session_state.uploaded_files[key].name, TAB_PROPS_MAP[key])
        
        st.markdown("---") # 왼쪽 컬럼의 끝 구분선

    # --- 2. 오른쪽 컬럼 (QC 요약 테이블) ---
    with table_col:
        st.subheader("QC 결과 요약")
        st.caption("선택된 필터에 따라 동적으로 변경됩니다.")
        
        # 요약 테이블 출력 로직
        df_pcb_filtered = st.session_state.get('filtered_df_Pcb')
        
        if st.session_state.show_summary_table:
            
            selected_fields_for_table = st.session_state.get(f'detail_fields_select_Pcb', [])
            
            if df_pcb_filtered is not None and not df_pcb_filtered.empty:
                # 테이블 생성 함수 호출
                generate_dynamic_summary_table(df_pcb_filtered, selected_fields_for_table)
            else:
                st.warning("테이블을 표시할 데이터가 없거나 필터링 결과 0건입니다.")
                # st.session_state.show_summary_table = False # 플래그 해제
                
    # --------------------------
    # FOOTER 영역 시작 
    # --------------------------
    st.markdown("---")
    st.markdown("데이터 분석 툴 v1.0 | Google Gemini 기반 분석") 
    st.markdown("---")


if __name__ == "__main__":
    main()
