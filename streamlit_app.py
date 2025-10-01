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
    """
    [수정됨] 필터링된 DataFrame을 일별/Jig별로 분리하여 테스트 항목별 QC 결과 요약 테이블을 생성합니다.
    """
    if df.empty:
        st.warning("필터링된 데이터가 없어 요약 테이블을 생성할 수 없습니다.")
        return

    # 1. QC 컬럼 식별: selected_fields 중 '_QC'로 끝나는 유효한 컬럼만 통계에 사용합니다.
    qc_columns = [col for col in selected_fields if col.endswith('_QC') and col in df.columns and df[col].dtype == object]
    
    if not qc_columns:
        st.warning("테이블 생성 불가: '상세 내역'에서 _QC로 끝나는 품질 관리 컬럼을 1개 이상 선택해 주세요.")
        return

    # 분석 키가 'Pcb'이므로 해당 Jig 컬럼과 Timestamp 컬럼을 가정합니다.
    # [주의] 이 정보는 실제로는 config.py나 analysis_main에서 가져와야 하지만, 빠른 구현을 위해 하드코딩합니다.
    JIG_COL = 'PcbMaxIrPwr' 
    TIMESTAMP_COL = 'PcbStartTime' 

    if TIMESTAMP_COL not in df.columns:
        st.error(f"테이블 생성 실패: 필수 컬럼 '{TIMESTAMP_COL}'이 데이터프레임에 없습니다.")
        return

    # 2. 상태 매핑: '데이터 부족'은 '제외'로 처리
    status_map = {
        'Pass': 'Pass',
        '미달': '미달 (Under)',
        '초과': '초과 (Over)',
        '제외': '제외 (Excluded)',
        '데이터 부족': '제외 (Excluded)' 
    }
    
    # 3. 데이터프레임 준비 및 그룹핑
    
    # TIMESTAMP_COL을 날짜 객체로 변환하여 'Date' 컬럼 생성
    try:
        df['Date'] = pd.to_datetime(df[TIMESTAMP_COL], errors='coerce').dt.date
    except Exception:
        st.error(f"날짜 컬럼({TIMESTAMP_COL}) 변환 실패. 데이터 형식을 확인하세요.")
        return
        
    # 'Jig' 컬럼 복사
    df['Jig'] = df[JIG_COL]
    
    # 통계를 저장할 빈 리스트
    summary_data_list = []
    
    # 4. 일별, Jig별, 테스트 항목별 그룹핑 및 통계 계산
    
    # 모든 QC 컬럼을 한 번에 녹여(melt) 행을 만듭니다.
    df_melted = df.melt(
        id_vars=['Date', 'Jig'], 
        value_vars=qc_columns, 
        var_name='QC_Test_Col', 
        value_name='Status'
    )
    
    # 매핑되지 않은 상태값(nan 등)을 제외
    df_melted = df_melted.dropna(subset=['Status'])
    
    # 상태값 매핑 (미달/초과/제외 등)
    df_melted['Mapped_Status'] = df_melted['Status'].apply(lambda x: status_map.get(x, '제외 (Excluded)'))
    
    # 그룹별 카운트 계산: Date, Jig, QC_Test_Col, Mapped_Status 별로 행 수를 계산
    df_grouped = df_melted.groupby(
        ['Date', 'Jig', 'QC_Test_Col', 'Mapped_Status'], 
        dropna=False
    ).size().reset_index(name='Count')
    
    # 5. 최종 요약 테이블 생성
    
    # 'QC_Test_Col' 이름을 'Test'로 변환
    df_grouped['Test'] = df_grouped['QC_Test_Col'].str.replace('_QC', '')

    # Date, Jig, Test를 기준으로 피벗 테이블 생성
    df_pivot = df_grouped.pivot_table(
        index=['Date', 'Jig', 'Test'], 
        columns='Mapped_Status', 
        values='Count', 
        fill_value=0
    ).reset_index()

    # 필요한 컬럼이 없으면 0으로 채우기 (Pass, 미달, 초과 등)
    required_cols = ['Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    for col in required_cols:
        if col not in df_pivot.columns:
            df_pivot[col] = 0

    # Total 및 Failure 계산
    df_pivot['Total'] = df_pivot[required_cols].sum(axis=1)
    df_pivot['Failure'] = df_pivot['미달 (Under)'] + df_pivot['초과 (Over)']
    
    # Failure Rate 계산
    df_pivot['Failure Rate (%)'] = (df_pivot['Failure'] / df_pivot['Total'] * 100).apply(
        lambda x: f"{x:.1f}%" if x == x else "0.0%" # NaN 방지
    )
    
    # 결과 테이블 컬럼 순서 조정
    final_cols = ['Date', 'Jig', 'Test', 'Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)', 'Total', 'Failure', 'Failure Rate (%)']
    df_summary = df_pivot[final_cols].sort_values(by=['Date', 'Jig', 'Test'])

    # 6. Streamlit에 출력
    st.markdown("---")
    st.subheader("PCB 테스트 항목별 QC 결과 요약 테이블 (일별/Jig별)")
    st.dataframe(df_summary)
    st.markdown("---")

# ==============================
# 메인 실행 함수
# ... (main 함수는 변경 없음)
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
    # MAIN 영역 상하 분할 시작
    # --------------------------
    
    # --- 1. 상단 영역 (QC 요약 테이블) ---
    st.header("QC 요약 테이블")
    
    df_pcb_filtered = st.session_state.get('filtered_df_Pcb')
    
    if st.session_state.show_summary_table:
        
        selected_fields_for_table = st.session_state.get(f'detail_fields_select_Pcb', [])
        
        if df_pcb_filtered is not None and not df_pcb_filtered.empty:
            # 테이블 생성 함수 호출
            generate_dynamic_summary_table(df_pcb_filtered, selected_fields_for_table)
        else:
            st.error("테이블 생성 실패: 필터링된 PCB 데이터가 없거나 비어 있습니다. 'Pcb 분석 실행'을 확인하고 필터(날짜/Jig)를 해제해보세요.")
            st.session_state.show_summary_table = False 
            
    st.markdown("---") 
    
    # --- 2. 하단 영역 (분석 실행 및 상세 내역) ---
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
            # 상세 분석 결과
            display_analysis_result(key, st.session_state.uploaded_files[key].name, TAB_PROPS_MAP[key])
            
    # --------------------------
    # FOOTER 영역 시작 
    # --------------------------
    st.markdown("---")
    st.markdown("데이터 분석 툴 v1.0 | Google Gemini 기반 분석") 
    st.markdown("---")


if __name__ == "__main__":
    main()
