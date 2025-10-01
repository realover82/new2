import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt
from typing import Dict # NameError 해결

# 1. 기능별 분할된 모듈 임포트
from config import ANALYSIS_KEYS, TAB_PROPS_MAP
from analysis_main import display_analysis_result 
from chart_generator import create_stacked_bar_chart # Altair 차트 모듈

# 2. 각 CSV 분석 모듈 임포트 (기존 코드 유지)
from csv2 import read_csv_with_dynamic_header, analyze_data
from csv_Fw import read_csv_with_dynamic_header_for_Fw, analyze_Fw_data
from csv_RfTx import read_csv_with_dynamic_header_for_RfTx, analyze_RfTx_data
from csv_Semi import read_csv_with_dynamic_header_for_Semi, analyze_Semi_data
from csv_Batadc import read_csv_with_dynamic_header_for_Batadc, analyze_Batadc_data

# ==============================
# 콜백 함수 정의 (생략)
# ==============================
def set_show_table_true():
    st.session_state.show_summary_table = True
    st.session_state.show_chart = False
    
def set_show_table_false():
    st.session_state.show_summary_table = False
    st.session_state.show_chart = False
    
def set_show_chart_only_true():
    st.session_state.show_chart = True
    st.session_state.show_summary_table = False 

def set_show_chart_false():
    st.session_state.show_chart = False
    
def set_hide_all():
    st.session_state.show_summary_table = False
    st.session_state.show_chart = False

# ==============================
# 동적 요약 테이블 생성 함수 (생략)
# ==============================
def generate_dynamic_summary_table(df: pd.DataFrame, selected_fields: list, props: Dict[str, str]):
    # ... (함수 내용은 변경 없음, 정상 작동 가정)
    if df.empty:
        st.warning("필터링된 데이터가 없어 요약 테이블을 생성할 수 없습니다.")
        return

    # 1. QC 컬럼 식별: selected_fields 중 '_QC'로 끝나는 유효한 컬럼만 통계에 사용합니다.
    qc_columns = [col for col in selected_fields if col.endswith('_QC') and col in df.columns and df[col].dtype == object]
    
    if not qc_columns:
        st.warning("테이블 생성 불가: '상세 내역'에서 _QC로 끝나는 품질 관리 컬럼을 1개 이상 선택해 주세요.")
        st.session_state['summary_df_for_chart'] = None
        return

    # (중략: 데이터 처리 및 집계 로직)
    status_map = { 'Pass': 'Pass', '미달': '미달 (Under)', '초과': '초과 (Over)', '제외': '제외 (Excluded)', '데이터 부족': '제외 (Excluded)' }
    summary_data_list = []
    
    JIG_COL = props['jig_col']
    TIMESTAMP_COL = props['timestamp_col']
    
    # ... (데이터 준비 및 그룹핑 로직)
    df['Date'] = pd.to_datetime(df[TIMESTAMP_COL], errors='coerce').dt.date
    df['Jig'] = df[JIG_COL]
    
    df_melted = df.melt(id_vars=['Date', 'Jig'], value_vars=qc_columns, var_name='QC_Test_Col', value_name='Status')
    df_melted = df_melted.dropna(subset=['Status'])
    df_melted['Mapped_Status'] = df_melted['Status'].apply(lambda x: status_map.get(x, '제외 (Excluded)'))
    
    df_grouped = df_melted.groupby(['Date', 'Jig', 'QC_Test_Col', 'Mapped_Status'], dropna=False).size().reset_index(name='Count')
    
    df_grouped['Test'] = df_grouped['QC_Test_Col'].str.replace('_QC', '')
    df_pivot = df_grouped.pivot_table(index=['Date', 'Jig', 'Test'], columns='Mapped_Status', values='Count', fill_value=0).reset_index()

    required_cols = ['Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    for col in required_cols:
        if col not in df_pivot.columns: df_pivot[col] = 0

    df_pivot['Total'] = df_pivot[required_cols].sum(axis=1)
    df_pivot['Failure'] = df_pivot['미달 (Under)'] + df_pivot['초과 (Over)']
    df_pivot['Failure Rate (%)'] = (df_pivot['Failure'] / df_pivot['Total'] * 100).apply(lambda x: f"{x:.1f}%" if x == x else "0.0%")
    
    final_cols = ['Date', 'Jig', 'Test', 'Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)', 'Total', 'Failure', 'Failure Rate (%)']
    summary_df = df_pivot[final_cols].sort_values(by=['Date', 'Jig', 'Test'])
    
    # 5. Streamlit에 출력 및 차트 데이터 저장
    st.subheader("PCB 테스트 항목별 QC 결과 요약 테이블 (일별/Jig별)")
    st.dataframe(summary_df.set_index(['Date', 'Jig', 'Test']))
    st.markdown("---")
    
    # 차트 생성을 위해 summary_df를 세션 상태에 저장합니다.
    st.session_state['summary_df_for_chart'] = summary_df # 이 DF가 차트 생성 함수의 입력이 됩니다.


# ==============================
# 메인 실행 함수
# ==============================
def main():
    st.set_page_config(layout="wide")
    
    # (중략: HEADER, 세션 초기화, tab_map 정의)
    st.title("리모컨 생산 데이터 분석 툴") 
    st.markdown("---")
    
    # (세션 초기화 및 tab_map 정의 로직)
    # ...
    
    ANALYSIS_KEYS = ['Pcb', 'Fw', 'RfTx', 'Semi', 'Batadc']
    if 'show_summary_table' not in st.session_state: st.session_state.show_summary_table = False
    if 'show_chart' not in st.session_state: st.session_state.show_chart = False
    
    tab_map = {} # 실제 코드에서는 채워져 있다고 가정

    # 1. 사이드바 로직 (생략)
    # ...
    # 2. 사이드바: 테이블/차트 표시 버튼 배치 
    # ... (생략)
    st.sidebar.title("분석 항목 선택")
    
    analysis_options = {key: f"파일 {key} 분석" for key in ANALYSIS_KEYS}
    default_key = st.session_state.get('last_selected_analysis_key', 'Pcb')
    
    selected_analysis_label = st.sidebar.radio(
        "분석할 데이터 선택", 
        list(analysis_options.values()),
        index=list(map(str.upper, ANALYSIS_KEYS)).index('PCB'), # PCB가 0번 인덱스라고 가정
        key='analysis_radio'
    )
    
    selected_key = 'Pcb' # 디버깅을 위해 Pcb로 고정한다고 가정
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("QC 결과 시각화")

    df_pcb = st.session_state.analysis_results.get('Pcb')
    
    # [수정된 버튼 로직 시작]
    if df_pcb is not None and not df_pcb.empty:
        # 2-A. 테이블 버튼
        if st.session_state.show_summary_table:
            st.sidebar.button("테이블 숨기기", on_click=set_show_table_false, key='hide_pcb_table')
        else:
            st.sidebar.button("PCB 요약 테이블 보기", on_click=set_show_table_true, key='show_pcb_table_btn')
            
        # 2-B. 차트 버튼
        if st.session_state.show_chart:
            st.sidebar.button("차트 숨기기", on_click=set_show_chart_false, key='hide_pcb_chart')
        else:
            st.sidebar.button("PCB 요약 차트 보기", on_click=set_show_chart_only_true, key='show_pcb_chart_btn')
            
        # 2-C. 모두 숨기기 버튼
        if st.session_state.show_summary_table or st.session_state.show_chart:
            st.sidebar.button("모두 숨기기", on_click=set_hide_all, key='hide_all_results')
        
    else:
        st.sidebar.warning("'파일 Pcb 분석' 실행 후 버튼이 나타납니다.")
    # [수정된 버튼 로직 끝]

    # (중략: MAIN 영역 시작)
    st.markdown("---")
    st.markdown("## [Main Content Start]")
    st.markdown("---")
    
    df_pcb_filtered = st.session_state.get('filtered_df_Pcb')
    selected_fields_for_table = st.session_state.get(f'detail_fields_select_Pcb', [])
    
    # [차트/테이블 출력 시작]
    if df_pcb_filtered is not None and not df_pcb_filtered.empty:
        
        # A) 테이블 출력 로직
        if st.session_state.show_summary_table:
            generate_dynamic_summary_table(df_pcb_filtered, selected_fields_for_table, TAB_PROPS_MAP['Pcb'])
            
        # B) 차트 출력 로직 (테이블 아래에 생성)
        if st.session_state.show_chart:
            summary_df = st.session_state.get('summary_df_for_chart') 
            
            # --- 디버깅 코드 (이전 단계의 문제 해결) ---
            if summary_df is not None and not summary_df.empty:
                st.subheader("QC 결과 누적 막대 그래프")
                try:
                    chart_figure = create_stacked_bar_chart(summary_df, 'PCB')
                    if chart_figure:
                        st.altair_chart(chart_figure, use_container_width=True) 
                    else:
                        st.error("그래프 생성 중 오류가 발생했습니다.")
                except Exception as e:
                    st.error(f"그래프 렌더링 중 오류 발생: {e}")
            else:
                 st.warning("차트를 생성할 요약 데이터(테이블 내용)가 없습니다. 먼저 테이블을 확인하거나 필터를 해제해 주세요.")
        
    elif st.session_state.show_summary_table or st.session_state.show_chart:
        st.error("결과 생성 실패: PCB 분석 데이터가 없거나 필터링 결과 0건입니다.")
        set_hide_all()
    # [차트/테이블 출력 끝]

    # (중략: 하단 영역, 파일 업로드 및 분석 실행, FOOTER 로직)
    # ...

if __name__ == "__main__":
    main()