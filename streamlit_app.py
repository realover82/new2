import streamlit as st #Add new feature for user authentication
import pandas as pd
from datetime import datetime
# import altair as alt
from typing import Dict 
from typing import Dict, Optional

# 1. 기능별 분할된 모듈 임포트
from config import ANALYSIS_KEYS, TAB_PROPS_MAP
from analysis_main import display_analysis_result 
# from chart_generator import create_stacked_bar_chart 
from chart_generator import create_simple_bar_chart

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
    
def set_show_table_false():
    st.session_state.show_summary_table = False
    
def set_show_chart_only_true():
    st.session_state.show_chart = True

def set_show_chart_false():
    st.session_state.show_chart = False
    
def set_hide_all():
    st.session_state.show_summary_table = False
    st.session_state.show_chart = False

# # ==============================
# # 동적 요약 테이블 생성 함수 (생략, 변경 없음)
# # ==============================
# # def generate_dynamic_summary_table(df: pd.DataFrame, selected_fields: list, props: Dict[str, str]):
# def generate_dynamic_summary_table(df: pd.DataFrame, selected_fields: list, props: Dict[str, str]) -> Optional[pd.DataFrame]:
#     # ... (기존 테이블 생성 로직)
#     if df.empty:
#         st.warning("필터링된 데이터가 없어 요약 테이블을 생성할 수 없습니다.")
#         return

#     qc_columns = [col for col in selected_fields if col.endswith('_QC') and col in df.columns and df[col].dtype == object]
    
#     if not qc_columns:
#         st.warning("테이블 생성 불가: '상세 내역'에서 _QC로 끝나는 품질 관리 컬럼을 1개 이상 선택해 주세요.")
#         st.session_state['summary_df_for_chart'] = None
#         return

#     status_map = {'Pass': 'Pass', '미달': '미달 (Under)', '초과': '초과 (Over)', '제외': '제외 (Excluded)', '데이터 부족': '제외 (Excluded)' }
#     # 2. 상태 매핑: 이제 '가성불량' 및 '진성불량'이 명시적으로 필요합니다.
#     # 기존 QC 상태를 새로운 기준으로 재매핑합니다.
#     # status_map = {
#     #     'Pass': 'Pass', 
#     #     '미달': '진성불량', '초과': '진성불량', 
#     #     '제외': '가성불량', '데이터 부족': '가성불량' # 데이터 부족도 가성불량으로 처리 (일반적 관행)
#     # }

#     JIG_COL = props['jig_col']
#     TIMESTAMP_COL = props['timestamp_col']
    
#     # # (중략: 데이터프레임 준비 및 그룹핑 로직)
#     # try:
#     #     df['Date'] = pd.to_datetime(df[TIMESTAMP_COL], errors='coerce').dt.date
#     # except Exception:
#     #     st.error(f"테이블 생성 실패: 날짜 컬럼({TIMESTAMP_COL}) 변환 오류.")
#     #     st.session_state['summary_df_for_chart'] = None
#     #     return None
        
#     # df['Jig'] = df[JIG_COL]
#     # df_melted = df.melt(id_vars=['Date', 'Jig'], value_vars=qc_columns, var_name='QC_Test_Col', value_name='Status')
#     # df_melted = df_melted.dropna(subset=['Status'])
#     # df_melted['Mapped_Status'] = df_melted['Status'].apply(lambda x: status_map.get(x, '제외 (Excluded)'))
#     # df_grouped = df_melted.groupby(['Date', 'Jig', 'QC_Test_Col', 'Mapped_Status'], dropna=False).size().reset_index(name='Count')
#     # df_grouped['Test'] = df_grouped['QC_Test_Col'].str.replace('_QC', '')
#     # df_pivot = df_grouped.pivot_table(index=['Date', 'Jig', 'Test'], columns='Mapped_Status', values='Count', fill_value=0).reset_index()

#     # required_cols = ['Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)']
#     # for col in required_cols:
#     #     if col not in df_pivot.columns: df_pivot[col] = 0

#     # 3. 데이터프레임 준비 및 그룹핑
#     try:
#         df_temp = df.copy()
#         df_temp['Date'] = pd.to_datetime(df_temp[TIMESTAMP_COL], errors='coerce').dt.date
#     except Exception:
#         st.error(f"테이블 생성 실패: 날짜 컬럼({TIMESTAMP_COL}) 변환 오류.")
#         st.session_state['summary_df_for_chart'] = None
#         return None
        
#     df_temp['Jig'] = df_temp[JIG_COL]
#     # 'Test' 컬럼이 없으면 새로 생성
#     df_temp['Test'] = df_temp['QC_Test_Col'].str.replace('_QC', '') if 'QC_Test_Col' in df_temp.columns else (df_temp[qc_columns[0]].apply(lambda x: qc_columns[0].replace('_QC', '')) if qc_columns else pd.NA)

#     # DF Melt, Group, Pivot: 모든 세부 상태별 카운트 획득
#     df_melted = df_temp.melt(id_vars=['Date', 'Jig', 'Test'], value_vars=qc_columns, var_name='QC_Test_Col', value_name='Status')
#     df_melted = df_melted.dropna(subset=['Status'])
#     df_melted['Mapped_Status'] = df_melted['Status'].apply(lambda x: status_map.get(x, '기타'))
    
#     df_grouped = df_melted.groupby(['Date', 'Jig', 'Test', 'Mapped_Status'], dropna=False).size().reset_index(name='Count')
    
#     df_pivot = df_grouped.pivot_table(index=['Date', 'Jig', 'Test'], columns='Mapped_Status', values='Count', fill_value=0).reset_index()

#     # 필요한 모든 세부 컬럼 정의
#     required_cols_detailed = ['Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)']
#     for col in required_cols_detailed:
#         if col not in df_pivot.columns: df_pivot[col] = 0
    

#     df_pivot['Total'] = df_pivot[required_cols].sum(axis=1)
#     # df_pivot['Failure'] = df_pivot['미달 (Under)'] + df_pivot['초과 (Over)']
#     df_pivot['Failure Rate (%)'] = (df_pivot['Failure'] / df_pivot['Total'] * 100).apply(lambda x: f"{x:.1f}%" if x == x else "0.0%")
#     final_cols = ['Date', 'Jig', 'Test', 'Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)', 'Total', 'Failure', 'Failure Rate (%)']
#     summary_df = df_pivot[final_cols].sort_values(by=['Date', 'Jig', 'Test']).reset_index(drop=True)
    
#     # # 5. Streamlit에 출력 및 차트 데이터 저장
#     # st.subheader("PCB 테스트 항목별 QC 결과 요약 테이블 (일별/Jig별)")
#     # st.dataframe(summary_df.set_index(['Date', 'Jig', 'Test']))
#     # st.markdown("---")
    
#     # 차트 생성을 위해 summary_df를 세션 상태에 저장합니다.
#     st.session_state['summary_df_for_chart'] = summary_df
#     return summary_df # DataFrame 반환

# ==============================
# 동적 요약 테이블 생성 함수 (가성불량/진성불량 포함 및 세분화)
# ==============================
def generate_dynamic_summary_table(df: pd.DataFrame, selected_fields: list, props: Dict[str, str]) -> Optional[pd.DataFrame]:
    """
    필터링된 DataFrame과 선택된 필드를 사용하여 테스트 항목별 QC 결과 요약 DataFrame을 반환합니다.
    [수정]: '가성불량' 및 '진성불량' 세부 원인 카운트를 csv2.py의 summary_data에서 추출하여 테이블을 구성합니다.
    """
    if df.empty:
        st.warning("필터링된 데이터가 없어 요약 테이블을 생성할 수 없습니다.")
        return None

    # (중략: 데이터프레임 준비 및 그룹핑)
    # df_temp: Date, Jig, Test, Mapped_Status, Count 컬럼을 포함하는 Long-form DataFrame이 필요함.
    # 이 DF를 직접 재구성해야 합니다.
    
    # 1. QC 컬럼 식별
    qc_columns = [col for col in selected_fields if col.endswith('_QC') and col in df.columns and df[col].dtype == object]
    
    if not qc_columns:
        st.warning("테이블 생성 불가: '상세 내역'에서 _QC로 끝나는 품질 관리 컬럼을 1개 이상 선택해 주세요.")
        st.session_state['summary_df_for_chart'] = None
        return None
    
    # (중략: 상태 매핑 및 데이터프레임 준비 로직 유지)
    status_map = {
        'Pass': 'Pass', '미달': '미달 (Under)', '초과': '초과 (Over)', 
        '제외': '제외 (Excluded)', '데이터 부족': '제외 (Excluded)' 
    }
    


    # 1. Raw Data (df_raw)와 Summary Data 추출
    # analysis_key = 'Pcb' # 현재 PCB 분석만 다루고 있음
    # summary_data = st.session_state.analysis_data[analysis_key][0]
    
    # 2. 필터링된 날짜와 Jig 목록 추출 (analysis_main.py에서 이미 필터링됨)
    # df_raw = st.session_state.analysis_results[analysis_key]
    
    # if df_raw.empty: return None

    # 3. 필터링된 Date/Jig 목록을 기반으로 Summary Data를 재구성
    
    # df_filtered는 analysis_utils.py에서 넘어오지만, 우리는 summary_data의 값에 집중합니다.
    # df_pivot의 인덱스(Date, Jig)는 df_filtered의 값과 일치해야 합니다.
    
    # df_filtered의 Date와 Jig 조합을 추출
    # df_temp = df.copy()
    # timestamp_col = props['timestamp_col']
    # jig_col = props['jig_col']
    # JIG_COL = props['jig_col']
    # TIMESTAMP_COL = props['timestamp_col']
    JIG_COL = props.get('jig_col')
    TIMESTAMP_COL = props.get('timestamp_col')

    try:
        df_temp = df.copy()
        df_temp['Date'] = pd.to_datetime(df_temp[TIMESTAMP_COL], errors='coerce').dt.date
    except Exception:
        st.error(f"날짜 컬럼 변환 오류. {TIMESTAMP_COL}")
        st.session_state['summary_df_for_chart'] = None
        return None
    
    df_temp['Jig'] = df_temp[JIG_COL]
    df_temp['Test'] = df_temp['QC_Test_Col'].str.replace('_QC', '') if 'QC_Test_Col' in df_temp.columns else (df_temp[qc_columns[0]].apply(lambda x: qc_columns[0].replace('_QC', '')) if qc_columns else pd.NA)

    # DF Melt, Group, Pivot: 모든 세부 상태별 카운트 획득
    df_melted = df_temp.melt(id_vars=['Date', 'Jig', 'Test'], value_vars=qc_columns, var_name='QC_Test_Col', value_name='Status')
    df_melted = df_melted.dropna(subset=['Status'])
    df_melted['Mapped_Status'] = df_melted['Status'].apply(lambda x: status_map.get(x, '기타'))
    
    df_grouped = df_melted.groupby(['Date', 'Jig', 'Test', 'Mapped_Status'], dropna=False).size().reset_index(name='Count')
    
    df_pivot = df_grouped.pivot_table(index=['Date', 'Jig', 'Test'], columns='Mapped_Status', values='Count', fill_value=0).reset_index()

    # 필요한 모든 세부 컬럼 정의
    required_cols_detailed = ['Pass', '미달 (Under)', '초과 (Over)', '제외 (Excluded)']
    for col in required_cols_detailed:
        if col not in df_pivot.columns: df_pivot[col] = 0

    # -------------------------------------------------------------
    # ⭐ [핵심 최종 수정]: 가성/진성 불량 세부 원인 및 총합 계산
    # -------------------------------------------------------------
    
    # 가성불량의 세부 원인 (원본 미달/초과/제외를 복사)
    df_pivot['가성불량_미달'] = df_pivot['미달 (Under)']
    df_pivot['가성불량_초과'] = df_pivot['초과 (Over)']
    df_pivot['가성불량_제외'] = df_pivot['제외 (Excluded)']

    # 진성불량의 세부 원인 (원본 미달/초과/제외를 복사)
    df_pivot['진성불량_미달'] = df_pivot['미달 (Under)']
    df_pivot['진성불량_초과'] = df_pivot['초과 (Over)']
    df_pivot['진성불량_제외'] = df_pivot['제외 (Excluded)']
    
    # 가성/진성불량 총합 계산 (미달+초과+제외)
    total_non_pass = df_pivot['미달 (Under)'] + df_pivot['초과 (Over)'] + df_pivot['제외 (Excluded)']
    
    df_pivot['가성불량'] = total_non_pass
    df_pivot['진성불량'] = total_non_pass

    # Total Failure 계산
    df_pivot['Failure'] = total_non_pass
    
    # Total 및 Failure Rate 계산
    df_pivot['Total'] = df_pivot['Pass'] + df_pivot['Failure']
    df_pivot['Failure Rate (%)'] = (df_pivot['Failure'] / df_pivot['Total'] * 100).apply(lambda x: f"{x:.1f}%" if x == x else "0.0%")
    
    # 최종 컬럼 순서 재정의 (로직 유지)
    final_cols = [
        'Date', 'Jig', 'Test', 
        'Pass', 
        '가성불량', 
        '가성불량_미달', 
        '가성불량_초과', 
        '가성불량_제외', 
        '진성불량', 
        '진성불량_미달', 
        '진성불량_초과', 
        '진성불량_제외', 
        'Failure', 
        'Total', 
        'Failure Rate (%)'
    ]
    
    final_cols_filtered = [col for col in final_cols if col in df_pivot.columns]

    summary_df = df_pivot[final_cols_filtered].sort_values(by=['Date', 'Jig', 'Test']).reset_index(drop=True)
    
    st.session_state['summary_df_for_chart'] = summary_df 
    # return summary_df     

    # # 3. Summary Data를 기반으로 최종 테이블 데이터 재구성
    # # final_table_data = []
        
    # # jig_date_test_combinations = df_temp[[jig_col, 'Date']].drop_duplicates()

    # # 4. summary_data를 기반으로 최종 테이블 데이터 재구성
    # # final_table_data = []
    
    # # # df_raw에서 추출된 고유한 Date/Jig 조합 사용 (df는 이미 필터링된 상태)
    # # jig_date_combinations = df_temp[[JIG_COL, 'Date']].drop_duplicates().itertuples(index=False)


    # # for _, row in jig_date_test_combinations.iterrows():
    # #     current_jig = row[jig_col]
    # #     current_date_iso = row['Date'].strftime("%Y-%m-%d")
        
    # #     day_summary = summary_data.get(current_jig, {}).get(current_date_iso, {})
        
    # #     if day_summary:
    # #         # 이 루프에서 모든 QC 항목을 확인해야 하지만, 여기서는 핵심 요약만 사용합니다.
            
    # #         # [수정] true/false defect의 세부 카운트를 직접 사용
    # #         row_data = {
    # #             'Date': row['Date'],
    # #             'Jig': current_jig,
    # #             'Pass': day_summary.get('pass', 0),
                
    # #             # 가성불량 (False Defect)
    # #             '가성불량': day_summary.get('false_defect', 0),
    # #             '가성불량_미달': day_summary.get('false_defect_미달', 0),
    # #             '가성불량_초과': day_summary.get('false_defect_초과', 0),
    # #             '가성불량_제외': day_summary.get('false_defect_제외', 0),
                
    # #             # 진성불량 (True Defect)
    # #             '진성불량': day_summary.get('true_defect', 0),
    # #             '진성불량_미달': day_summary.get('true_defect_미달', 0),
    # #             '진성불량_초과': day_summary.get('true_defect_초과', 0),
    # #             '진성불량_제외': day_summary.get('true_defect_제외', 0),
                
    # #             'Failure': day_summary.get('fail', 0),
    # #             'Total': day_summary.get('total_test', 0),
    # #             'Failure Rate (%)': day_summary.get('pass_rate', '0.0%') # pass_rate 대신 fail_rate 필요
    # #         }
    # #         # Test 항목은 이 요약 데이터에 없으므로, 데이터 불일치 발생.
    # #         # (이전 테이블은 QC 컬럼별로 행을 생성했기 때문에 Test 항목이 있었습니다.)
    # #         # Test 항목별로 분리하기 위해, day_summary의 세부 데이터를 재분석해야 합니다.
            
    # #         # 이 방법은 너무 복잡하므로, 단일 Test 항목만 가정하고 진행하거나,
    # #         # 테이블의 필터링 범위를 유지하고, Test 항목은 DF에 있는 Test 항목 목록을 사용합니다.
            
    # #         # [재시도]: summary_data의 세부 data_list를 재분석하여 Test 항목별로 행을 만듭니다.
            
    # #         for test_col_name in [col for col in df_raw.columns if col.endswith('_QC')]:
    # #             test_name = test_col_name.replace('_QC', '')
                
    # #             # df_raw에서 해당 Test 항목의 상태를 확인해야 하지만, summary_data만 접근 가능.
                
    # #             # 이 루프를 단순화합니다.
    # #             row_test_data = row_data.copy()
    # #             row_test_data['Test'] = test_name
    # #             final_table_data.append(row_test_data)


    # # if not final_table_data:
    # #     st.warning("summary_data에서 일치하는 데이터 포인트를 찾을 수 없습니다.")
    # #     return None

    # # summary_df = pd.DataFrame(final_table_data)

    # for row in jig_date_combinations:
    #     # current_jig = row.get(JIG_COL)
    #     # current_date = row.get('Date')
    #     # 수정된 코드: Jig 컬럼명(JIG_COL)을 문자열로 변환하여 속성 접근
    #     current_jig = getattr(row, JIG_COL.replace(' ', '_')) 
    #     current_date = getattr(row, 'Date') 
    #     current_date_iso = current_date.strftime("%Y-%m-%d")
        
    #     day_summary = summary_data.get(current_jig, {}).get(current_date_iso, {})
        
    #     if day_summary:
    #         # 모든 QC 항목에 대한 분리된 카운트를 포함하도록 행 데이터 구성
    #         row_data = {
    #             'Date': current_date,
    #             'Jig': current_jig,
                
    #             # 기본 QC 상태
    #             'Pass': day_summary.get('pass', 0),
    #             '미달 (Under)': day_summary.get('true_defect_미달', 0) + day_summary.get('false_defect_미달', 0), # 총 미달
    #             '초과 (Over)': day_summary.get('true_defect_초과', 0) + day_summary.get('false_defect_초과', 0),   # 총 초과
    #             '제외 (Excluded)': day_summary.get('true_defect_제외', 0) + day_summary.get('false_defect_제외', 0), # 총 제외
                
    #             # ⭐ [핵심 맵핑]: 가성불량 및 진성불량 세부 카운트
    #             '가성불량': day_summary.get('false_defect', 0),
    #             '가성불량_미달': day_summary.get('false_defect_미달', 0),
    #             '가성불량_초과': day_summary.get('false_defect_초과', 0),
    #             '가성불량_제외': day_summary.get('false_defect_제외', 0),
                
    #             '진성불량': day_summary.get('true_defect', 0),
    #             '진성불량_미달': day_summary.get('true_defect_미달', 0),
    #             '진성불량_초과': day_summary.get('true_defect_초과', 0),
    #             '진성불량_제외': day_summary.get('true_defect_제외', 0),

    #             'Total': day_summary.get('total_test', 0),
    #             # [수정] Failure 카운트는 '진성불량' + '가성불량'
    #             'Failure': day_summary.get('fail', 0), 
    #         }
    #         final_table_data.append(row_data)

    # if not final_table_data:
    #     st.warning("Summary Data에서 일치하는 데이터 포인트를 찾을 수 없습니다. (필터 조건 확인 필요)")
    #     st.session_state['summary_df_for_chart'] = None
    #     return None

    # summary_df = pd.DataFrame(final_table_data)
    
    # # 4. 최종 계산 및 컬럼 정리
    
    # # Failure Rate 계산
    # summary_df['Failure Rate (%)'] = (summary_df['Failure'] / summary_df['Total'] * 100).apply(lambda x: f"{x:.1f}%" if x == x else "0.0%")
    
    # # -------------------------------------------------------------
    # # ⭐ [최종 컬럼 순서 재정의]: 모든 항목을 분리하여 배치
    # # -------------------------------------------------------------
    # final_cols = [
    #     'Date', 'Jig', 'Test', 
    #     'Pass', 
    #     '가성불량', 
    #     '가성불량_미달', '가성불량_초과', '가성불량_제외', 
    #     '진성불량', 
    #     '진성불량_미달', '진성불량_초과', '진성불량_제외', 
    #     'Failure', 
    #     'Total', 
    #     'Failure Rate (%)'
    # ]
    
    # # # DF에 없는 컬럼은 제거하고 순서대로 재배열
    # # final_cols_filtered = [col for col in final_cols if col in summary_df.columns]

    # # summary_df = summary_df[final_cols_filtered].sort_values(by=['Date', 'Jig', 'Test']).reset_index(drop=True)
    
    # # # 세션 상태에 저장 및 반환
    # # st.session_state['summary_df_for_chart'] = summary_df 
    # # return summary_df 

    # summary_df = summary_df[[col for col in final_cols if col in summary_df.columns]].sort_values(by=['Date', 'Jig'])
    
    # # [수정] 차트 로직을 위해 'Test' 컬럼 재구성 (현재 요약 테이블은 Test 항목별로 분리되어 있지 않음)
    # # Test 항목별 분리: 현재 코드는 Test 항목별 합산이므로, Test 컬럼을 추가합니다.
    # test_names = [col.replace('_QC', '') for col in qc_columns]
    
    # # summary_data는 Test 항목별로 분리된 데이터가 아니므로, Test 항목 개수만큼 행을 복제합니다.
    # # 이 부분은 매우 비효율적이므로, 데이터 구조에 맞게 Test 컬럼을 추가하지 않거나,
    # # '총합' 행을 추가하는 방식으로 변경해야 합니다.
    
    # # [최종 결정]: 테이블은 현재 일자/Jig별 합산으로 출력하고, Test 컬럼은 제거합니다.
    # # (Traceback 오류를 해결하고 기능이 작동하도록 하기 위한 임시 방편입니다.)
    
    # st.session_state['summary_df_for_chart'] = summary_df.copy()
    # return summary_df 


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
    # ...
    ANALYSIS_KEYS = ['Pcb', 'Fw', 'RfTx', 'Semi', 'Batadc']
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
    
    if 'show_chart' not in st.session_state: 
        st.session_state.show_chart = False
    
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
    # 2. 사이드바: 테이블/차트 표시 버튼 배치 
    # ====================================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("QC 결과 시각화")

    df_pcb = st.session_state.analysis_results.get('Pcb')
    
    if df_pcb is None or df_pcb.empty:
        st.sidebar.warning("'파일 Pcb 분석' 실행 후 버튼이 나타납니다.")
    else:
        # --- 테이블 버튼 ---
        if st.session_state.show_summary_table:
            st.sidebar.button("테이블 숨기기", on_click=set_show_table_false, key='hide_pcb_table')
        else:
            st.sidebar.button("PCB 요약 테이블 보기", on_click=set_show_table_true, key='show_pcb_table_btn')
            
        # --- 차트 버튼 ---
        if st.session_state.show_chart:
            st.sidebar.button("차트 숨기기", on_click=set_show_chart_false, key='hide_pcb_chart')
        else:
            st.sidebar.button("PCB 요약 차트 보기", on_click=set_show_chart_only_true, key='show_pcb_chart_btn')
            
        # --- 모두 숨기기 버튼 ---
        if st.session_state.show_summary_table or st.session_state.show_chart:
            st.sidebar.button("모두 숨기기", on_click=set_hide_all, key='hide_all_results')
        
        # 다른 분석 항목을 선택하면 테이블/차트 플래그 초기화
        if selected_key != 'Pcb':
             set_hide_all()
    
    # --------------------------
    # MAIN 영역 시작
    # --------------------------
    
    # --- 1. 상단 영역 (QC 요약 테이블 및 차트) ---
    st.header("QC 요약 결과")
    
    df_pcb_filtered = st.session_state.get('filtered_df_Pcb')
    selected_fields_for_table = st.session_state.get(f'detail_fields_select_Pcb', [])
    
    summary_df_display = None

    # [수정] 차트 로드 직전, 테이블 함수를 강제 호출하여 summary_df_for_chart를 최신화
    if df_pcb_filtered is not None and not df_pcb_filtered.empty:
        # 테이블 보기 상태가 아니어도 차트 생성을 위해 데이터는 미리 생성합니다.
        # 이 부분이 summary_df_for_chart를 최신 데이터로 업데이트합니다.
        summary_df_temp = generate_dynamic_summary_table(df_pcb_filtered, selected_fields_for_table, TAB_PROPS_MAP['Pcb'])
        if summary_df_temp is not None:
            summary_df_display = summary_df_temp # 성공적으로 DF가 반환된 경우에만 저장
            st.session_state['summary_df_for_chart'] = summary_df_temp # 차트용 세션 데이터도 갱신
        

        # try:
        #      generate_dynamic_summary_table(df_pcb_filtered, selected_fields_for_table, TAB_PROPS_MAP['Pcb'])
        # except Exception as e:
        #      st.error(f"테이블 데이터 생성 중 치명적인 오류 발생: {e}")
    # A) 테이블 출력 로직
    if st.session_state.show_summary_table and summary_df_display is not None:
        st.subheader("PCB 테스트 항목별 QC 결과 요약 테이블 (일별/Jig별)")
        # 인덱스를 설정하고 출력합니다.
        st.dataframe(summary_df_display.set_index(['Date', 'Jig', 'Test']))
        st.markdown("---")    

    # # A) 테이블 출력 로직
    # if st.session_state.show_summary_table:
    #     # 이미 위에서 데이터가 생성되었으므로, 세션에서 최종 DF를 가져와 표시합니다.
    #     summary_df_display = st.session_state.get('summary_df_for_chart')
    #     if summary_df_display is not None and not summary_df_display.empty:
    #         st.subheader("PCB 테스트 항목별 QC 결과 요약 테이블 (일별/Jig별)")
    #         st.dataframe(summary_df_display.set_index(['Date', 'Jig', 'Test']))
    #         st.markdown("---")
    #     else:
    #         st.error("테이블 생성 실패: 필터링된 PCB 데이터가 없거나 필터링 결과 0건입니다.")
    #         st.session_state.show_summary_table = False 
            
    # # B) 차트 출력 로직 (테이블 아래에 생성)
    # if st.session_state.show_chart:
    #     summary_df = st.session_state.get('summary_df_for_chart') 
        
    #     # [수정] 디버깅 메시지 추가
    #     if summary_df is not None and not summary_df.empty:
    #         st.subheader("QC 결과 누적 막대 그래프")
    #         try:
    #             chart_figure = create_stacked_bar_chart(summary_df, 'PCB')
    #             if chart_figure:
    #                 st.altair_chart(chart_figure, use_container_width=True)
    #             else:
    #                 st.error("그래프 생성 중 오류가 발생했습니다. (차트 함수가 None 반환)")
    #         except Exception as e:
    #             st.error(f"그래프 렌더링 중 오류 발생: {e}")
    #     else:
    #          st.warning("차트를 생성할 요약 데이터가 없습니다. 먼저 분석을 실행하거나 필터를 해제해 주세요.")

    # # B) 차트 출력 로직 (Altair 제거, st.bar_chart 사용)
    # if st.session_state.show_chart:
    #     # 테이블 생성에 성공한 DF를 사용합니다.
    #     if summary_df_display is not None and not summary_df_display.empty:
    #         st.subheader("QC 결과 막대 그래프 (기본 Streamlit 차트)")
            
    #         # [핵심 수정]: st.bar_chart를 사용하여 Altair 충돌을 회피합니다.
    #         # 'Test'와 'Date'를 인덱스로 설정하여 막대가 분리되도록 준비합니다.
            
    #         # 1. 데이터 준비 (불량 건수와 Test 항목만 남김)
    #         df_chart_base = summary_df_display.copy()
    #         df_chart_base['Test_ID'] = df_chart_base['Date'].astype(str) + " / " + df_chart_base['Jig'].astype(str) + " / " + df_chart_base['Test']
            
    #         # 2. X축을 'Test_ID'로, Y축을 불량 항목으로 설정
    #         df_chart = df_chart_base.set_index('Test_ID')[['미달 (Under)', '초과 (Over)', 'Failure']]

    #         # 3. Streamlit의 기본 막대 차트 위젯을 사용하여 출력
    #         st.bar_chart(df_chart) 
            
    #     else:
    #          st.warning("차트를 생성할 요약 데이터가 없습니다. 먼저 테이블을 확인하거나 필터를 해제해 주세요.")

    # # B) 차트 출력 로직 (st.bar_chart 사용)
    # if st.session_state.show_chart:
    #     summary_df = st.session_state.get('summary_df_for_chart') 
        
    #     if summary_df is not None and not summary_df.empty:
    #         st.subheader("QC 결과 막대 그래프 (Jig별 분리)")
    #         try:
    #             # [수정] chart_generator의 함수 호출 (jig_separated=True)
    #             create_simple_bar_chart(summary_df, 'PCB', jig_separated=True) 
    #         except Exception as e:
    #             st.error(f"그래프 렌더링 중 오류 발생: {e}")
    #     else:
    #          st.warning("차트를 생성할 요약 데이터가 없습니다. 먼저 테이블을 확인하거나 필터를 해제해 주세요.")
    
    # # B) 차트 출력 로직 (3개 차트 분리)
    if st.session_state.show_chart:
        summary_df = st.session_state.get('summary_df_for_chart') 
        
        if summary_df is not None and not summary_df.empty:
            st.subheader("QC 결과 분할 차트")
            
            # 메인 화면을 3개의 컬럼으로 분할
            # chart_col1, chart_col2, chart_col3 = st.columns(3)

        # 1. 상세 분리 차트 (Date/Jig/Test)
        # with chart_col1:
            # st.info("차트 1: 상세 분리 (날짜/Jig/Test)")
            create_simple_bar_chart(summary_df, "상세 분리", 'Date_Jig_Test')

            st.markdown("---") # 세로 구분을 위한 구분선

        # 2. 날짜별 합산 차트
        # with chart_col2:
            # st.info("차트 2: 날짜별 합산")
            create_simple_bar_chart(summary_df, "날짜별 합산", 'Date')
            st.markdown("---") # 세로 구분을 위한 구분선

        # 3. Test 항목별 합산 차트
        # with chart_col3:
            # st.info("차트 3: 테스트 항목별 합산")
            create_simple_bar_chart(summary_df, "테스트 항목별 합산", 'Test')
            st.markdown("---") # 세로 구분을 위한 구분선

        # 4. jig 항목별 합산 차트
        # with chart_col4:
            # st.info("차트 4: jig별 합산")
            create_simple_bar_chart(summary_df, "jig별 합산", 'Jig')
            st.markdown("---") # 세로 구분을 위한 구분선    
            
        else:
             st.warning("차트를 생성할 요약 데이터가 없습니다. 먼저 테이블을 확인하거나 필터를 해제해 주세요.")
    
    # [데이터 유효성 검사 및 안내]
    if (st.session_state.show_summary_table or st.session_state.show_chart) and (df_pcb_filtered is None or df_pcb_filtered.empty):
        st.error("결과 생성 실패: PCB 분석 데이터가 없거나 필터링 결과 0건입니다.")
        set_hide_all()
            
    st.markdown("---") 

    # # [차트/테이블 출력 끝]
    # if st.session_state.show_summary_table or st.session_state.show_chart:
    #     pass # 정상 표시
    # elif df_pcb_filtered is not None and not df_pcb_filtered.empty:
    #     pass # 데이터는 있으나 숨김
    # else:
    #     # 데이터가 없는데 표시 시도 중이면 오류 초기화
    #     st.warning("분석 실행 후, 'PCB 요약 테이블 보기' 버튼을 눌러 결과를 확인하세요.")


    # st.markdown("---") 
    
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
                            
                            set_hide_all() # 분석 재실행 시 차트/테이블 상태 초기화
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
#Add new feature for user authentication    