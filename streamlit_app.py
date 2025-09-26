import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

# 각 CSV 분석 모듈 불러오기
from csv2 import read_csv_with_dynamic_header, analyze_data
from csv_Fw import read_csv_with_dynamic_header_for_Fw, analyze_Fw_data
from csv_RfTx import read_csv_with_dynamic_header_for_RfTx, analyze_RfTx_data
from csv_Semi import read_csv_with_dynamic_header_for_Semi, analyze_Semi_data
from csv_Batadc import read_csv_with_dynamic_header_for_Batadc, analyze_Batadc_data

def display_analysis_result(analysis_key, file_name, props):
    """ session_state에 저장된 분석 결과를 Streamlit에 표시하는 함수 """
    if st.session_state.analysis_results[analysis_key] is None:
        st.error("데이터 로드에 실패했습니다. 파일 형식을 확인해주세요.")
        return

    # === 수정된 부분 1: analysis_data 유효성 검사 추가 ===
    if st.session_state.analysis_data[analysis_key] is None:
        st.error("데이터 분석에 실패했습니다. 분석 함수를 확인해주세요.")
        return
        
    summary_data, all_dates = st.session_state.analysis_data[analysis_key]
    df_raw = st.session_state.analysis_results[analysis_key]
    
    # 두 번째 수정: all_dates가 여전히 None일 경우를 처리
    if all_dates is None:
        st.error("데이터 분석에 실패했습니다. 날짜 관련 컬럼 형식을 확인해주세요.")
        return
    # =======================================================
    
    st.markdown(f"### '{file_name}' 분석 리포트")

    # === 수정된 부분 2: 필수 컬럼 존재 여부 확인 추가 ===
    required_columns = [props['jig_col'], props['timestamp_col']]
    missing_columns = [col for col in required_columns if col not in df_raw.columns]
    
    if missing_columns:
        st.error(f"데이터에 필수 컬럼이 없습니다: {', '.join(missing_columns)}. 파일을 다시 확인해주세요.")
        return
    # =======================================================
    
    # --- 기본 필터링 (Jig, 날짜 범위) ---
    st.subheader("기본 필터링")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        jig_list = sorted(df_raw[props['jig_col']].dropna().unique().tolist()) if props['jig_col'] in df_raw.columns else []
        selected_jig = st.selectbox("PC(Jig) 선택", ["전체"] + jig_list, key=f"select_{analysis_key}")
    
    if not all_dates:
        st.warning("분석할 데이터가 없습니다.")
        return
        
    min_date, max_date = min(all_dates), max(all_dates)
    with filter_col2:
        start_date = st.date_input("시작 날짜", min_value=min_date, max_value=max_date, value=min_date, key=f"start_date_{analysis_key}")
    with filter_col3:
        end_date = st.date_input("종료 날짜", min_value=min_date, max_value=max_date, value=max_date, key=f"end_date_{analysis_key}")

    if start_date > end_date:
        st.error("시작 날짜는 종료 날짜보다 이전이어야 합니다.")
        return

    filtered_dates = [d for d in all_dates if start_date <= d <= end_date]
    if not filtered_dates:
        st.warning("선택된 날짜 범위에 해당하는 데이터가 없습니다.")
        return

    st.write(f"**분석 시간**: {st.session_state.analysis_time[analysis_key]}")
    st.markdown("---")

    # --- 데이터 집계 ---
    jigs_to_display = jig_list if selected_jig == "전체" else [selected_jig]
    
    daily_aggregated_data = {}
    for date_obj in all_dates:
        daily_totals = {key: 0 for key in ['total_test', 'pass', 'false_defect', 'true_defect', 'fail']}
        for jig in jigs_to_display:
            data_point = summary_data.get(jig, {}).get(date_obj.strftime('%Y-%m-%d'))
            if data_point:
                for key in daily_totals:
                    daily_totals[key] += data_point.get(key, 0)
        daily_aggregated_data[date_obj] = daily_totals

    # --- 요약 (날짜 범위 요약 테이블) ---
    st.subheader("기간 요약")
    
    if filtered_dates:
        # 일별 집계 데이터를 DataFrame으로 변환
        summary_df_data = {
            '날짜': [d.strftime('%m-%d') for d in filtered_dates],
            '총 테스트 수': [daily_aggregated_data.get(d, {}).get('total_test', 0) for d in filtered_dates],
            'PASS': [daily_aggregated_data.get(d, {}).get('pass', 0) for d in filtered_dates],
            '가성불량': [daily_aggregated_data.get(d, {}).get('false_defect', 0) for d in filtered_dates],
            '진성불량': [daily_aggregated_data.get(d, {}).get('true_defect', 0) for d in filtered_dates],
            'FAIL': [daily_aggregated_data.get(d, {}).get('fail', 0) for d in filtered_dates]
        }
        summary_df = pd.DataFrame(summary_df_data).set_index('날짜')
        # 행/열을 바꿔서 표시 (transpose)
        st.dataframe(summary_df.transpose())
    else:
        st.info("선택된 조건에 해당하는 요약 데이터가 없습니다.")

    st.markdown("---")

    # --- 일별 추이 그래프 ---
    st.subheader("일자별 불량 추이")
    chart_mode_key = f'chart_mode_{analysis_key}'
    if chart_mode_key not in st.session_state:
        st.session_state[chart_mode_key] = 'bar'

    graph_cols = st.columns(2)
    with graph_cols[0]:
        if st.button("꺾은선 그래프", key=f"line_chart_btn_{analysis_key}"):
            st.session_state[chart_mode_key] = 'line'
    with graph_cols[1]:
        if st.button("막대 그래프", key=f"bar_chart_btn_{analysis_key}"):
            st.session_state[chart_mode_key] = 'bar'
    
    # 1. 모든 raw 데이터에서 필터링
    filtered_df_for_chart = df_raw[
        (df_raw[props['jig_col']].isin(jigs_to_display)) &
        (df_raw[props['timestamp_col']].dt.date.isin(filtered_dates))
    ].copy()
    
    # 'PassStatusNorm'이 'X'인 데이터만 남깁니다. (PASS 데이터 제외)
    filtered_df_for_chart = filtered_df_for_chart[filtered_df_for_chart['PassStatusNorm'] == 'X']
    # PassStatusNorm 컬럼을 추가한 코드 바로 아래에 삽입
    if 'PassStatusNorm' not in filtered_df_for_chart.columns:
        print("🚨🚨 오류: PassStatusNorm 컬럼이 DataFrame에 없습니다! 🚨🚨")
    else:
        print("✅ 성공: PassStatusNorm 컬럼이 존재합니다.")
        print("값 예시:", filtered_df_for_chart['PassStatusNorm'].head())

    # # 2. 시간별 데이터 집계
    # if not filtered_df_for_chart.empty:
    #     # 가성불량/진성불량 분리를 위해 SNumber의 PASS 기록을 미리 계산합니다.
    #     jig_pass_history = df_raw[df_raw['PassStatusNorm'] == 'O'].groupby(props['jig_col'])['SNumber'].unique().apply(set).to_dict()
    #     current_jig_passed_sns = jig_pass_history.get(selected_jig, set()) if selected_jig != "전체" else set(df_raw[df_raw['PassStatusNorm'] == 'O']['SNumber'].unique())
        
    #     # 가성/진성 불량 컬럼을 생성합니다.
    #     filtered_df_for_chart['불량 유형'] = filtered_df_for_chart['SNumber'].apply(
    #         lambda sn: '가성불량' if sn in current_jig_passed_sns else '진성불량'
    #     )

    #     # 시간대별/유형별로 그룹화하고 건수를 셉니다.
    #     chart_data_list = filtered_df_for_chart.groupby([
    #         pd.Grouper(key=props['timestamp_col'], freq='H'),
    #         '불량 유형'
    #     ]).size().reset_index(name='수량')
        
    #     # 'datetime' 컬럼의 날짜 부분과 시간 부분을 분리합니다.
    #     chart_data_list['날짜'] = chart_data_list[props['timestamp_col']].dt.date
    #     chart_data_list['시간'] = chart_data_list[props['timestamp_col']].dt.time

    # if not filtered_df_for_chart.empty:
    #     chart_df_melted = chart_data_list.rename(columns={props['timestamp_col']: 'datetime'})

    #     # Altair 차트 생성
    #     base = alt.Chart(chart_df_melted).encode(
    #         x=alt.X('시간:T', axis=alt.Axis(title='시간', format='%H:%M')),
    #         y=alt.Y('수량:Q', axis=alt.Axis(title='불량 건수'))
    #     ).properties(
    #         title='시간대별 불량 건수 추이'
    #     )
        
    #     # 라인 또는 막대 차트
    #     if st.session_state[chart_mode_key] == 'line':
    #         chart = base.mark_line(point=True).encode(
    #             color=alt.Color('불량 유형', legend=alt.Legend(title="불량 유형")),
    #             tooltip=['datetime:T', '불량 유형', '수량']
    #         )
    #     else: # 'bar'
    #         chart = base.mark_bar().encode(
    #             color=alt.Color('불량 유형', legend=alt.Legend(title="불량 유형")),
    #             tooltip=['datetime:T', '불량 유형', '수량']
    #         )
        
    #     # 날짜별로 그래프를 분할
    #     final_chart = chart.facet(
    #         column=alt.Column('날짜:N', header=alt.Header(titleOrient="bottom", labelOrient="bottom"))
    #     ).resolve_scale(
    #         x='independent',
    #         y='independent'
    #     )

    #     st.altair_chart(final_chart, use_container_width=False) # container_width를 False로 설정하여 가로 스크롤 가능하게 함
    # else:
    #     st.info("그래프를 표시할 데이터가 없습니다.")

    st.markdown("---")

    # --- 상세 내역 (일별) ---
    st.subheader("상세 내역 (일별)")
    
    # 1. 상세 내역 보기 제어용 세션 상태 변수 초기화
    if f'show_details_{analysis_key}' not in st.session_state:
        st.session_state[f'show_details_{analysis_key}'] = False

    # 2. 상세 내역 조회 버튼 추가
    if st.button("상세 내역 조회", key=f"show_details_btn_{analysis_key}"):
        st.session_state[f'show_details_{analysis_key}'] = True
        # 버튼을 누르면 기본적으로 '불량만 보기' 모드로 설정
        st.session_state[f'detail_mode_{analysis_key}'] = 'defects'

    # 3. 버튼이 눌리면 상세 내역 표시
    if st.session_state[f'show_details_{analysis_key}']:
        # 세션 상태에 상세 보기 모드를 저장할 변수를 초기화합니다.
        if f'detail_mode_{analysis_key}' not in st.session_state:
            st.session_state[f'detail_mode_{analysis_key}'] = 'all'

        # 상세 보기 모드 버튼을 생성합니다.
        detail_col1, detail_col2, detail_col3 = st.columns(3)
        with detail_col1:
            if st.button("전체 보기", key=f"detail_all_{analysis_key}"):
                st.session_state[f'detail_mode_{analysis_key}'] = 'all'
        with detail_col2:
            if st.button("불량만 보기", key=f"detail_defects_{analysis_key}"):
                st.session_state[f'detail_mode_{analysis_key}'] = 'defects'
        with detail_col3:
            if st.button("PASS만 보기", key=f"detail_pass_{analysis_key}"):
                st.session_state[f'detail_mode_{analysis_key}'] = 'pass'
        
        # 현재 상세 보기 모드에 따라 표시할 카테고리를 결정합니다.
        current_mode = st.session_state[f'detail_mode_{analysis_key}']
        
        for date_obj in filtered_dates:
            st.markdown(f"**{date_obj.strftime('%Y-%m-%d')}**")
            
            for jig in jigs_to_display:
                data_point = summary_data.get(jig, {}).get(date_obj.strftime('%Y-%m-%d'))
                if not data_point or data_point.get('total_test', 0) == 0:
                    continue

                st.markdown(f"**PC(Jig): {jig}**")
                
                # 현재 모드에 따라 표시할 카테고리 필터링
                if current_mode == 'defects':
                    categories = ['false_defect', 'true_defect']
                    labels = ['가성불량', '진성불량']
                elif current_mode == 'pass':
                    categories = ['pass']
                    labels = ['PASS']
                else: # 'all' 또는 특정 날짜 선택
                    categories = ['pass', 'false_defect', 'true_defect', 'fail']
                    labels = ['PASS', '가성불량', '진성불량', 'FAIL']

                for cat, label in zip(categories, labels):
                    full_data_list = data_point.get(f'{cat}_data', [])
                    
                    if not full_data_list:
                        continue

                    count = len(full_data_list)
                    unique_count = len(set(d['SNumber'] for d in full_data_list))

                    expander_title = f"{label} - {count}건 (중복값제거 SN: {unique_count}건)"
                    
                    with st.expander(expander_title, expanded=False):
                        fields_to_display = st.session_state.field_mapping.get(analysis_key, ['SNumber'])
                        
                        if not fields_to_display:
                            st.info("표시할 필드가 정의되지 않았습니다.")
                            continue

                        for item in full_data_list:
                            formatted_fields = [f"{field}: {item.get(field, 'N/A')}" for field in fields_to_display]
                            st.text(", ".join(formatted_fields))
            st.markdown("---")

    # --- DB 원본 확인 및 상세 검색 기능 ---
    st.subheader("DB 원본 상세 검색")
    search_col1, search_col2, search_col3 = st.columns([1, 2, 1])
    with search_col1:
        snumber_query = st.text_input("SNumber 검색", key=f"snumber_search_{analysis_key}")
    with search_col2:
        all_columns = df_raw.columns.tolist()
        selected_columns = st.multiselect("표시할 필드(열) 선택", all_columns, key=f"col_select_{analysis_key}")
    with search_col3:
        st.write("") 
        st.write("") 
        apply_button = st.button("필터 적용", key=f"apply_filter_{analysis_key}")

    filter_state_key = f'applied_filters_{analysis_key}'
    if apply_button:
        st.session_state[filter_state_key] = {
            'snumber': snumber_query,
            'columns': selected_columns
        }
    
    applied_filters = st.session_state.get(filter_state_key, {'snumber': '', 'columns': []})

    with st.expander("DB 원본 확인"):
        df_display = df_raw.copy()
        
        if applied_filters['snumber']:
            query = applied_filters['snumber']
            if 'SNumber' in df_display.columns and pd.api.types.is_string_dtype(df_display['SNumber']):
                df_display = df_display[df_display['SNumber'].str.contains(query, na=False, case=False)]
            else:
                try:
                    df_display = df_display[df_display.apply(lambda row: query.lower() in str(row.values).lower(), axis=1)]
                except Exception:
                    st.warning("SNumber 검색을 지원하지 않는 데이터 형식입니다.")

        if applied_filters['columns']:
            existing_cols = [col for col in applied_filters['columns'] if col in df_display.columns]
            df_display = df_display[existing_cols]
        
        st.dataframe(df_display)


# ==============================
# 메인 실행 함수
# ==============================
def main():
    st.set_page_config(layout="wide")
    st.title("리모컨 생산 데이터 분석 툴")
    st.markdown("---")

    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {k: None for k in ['Pcb', 'Fw', 'RfTx', 'Semi', 'Batadc']}
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {k: None for k in ['Pcb', 'Fw', 'RfTx', 'Semi', 'Batadc']}
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = {k: None for k in ['Pcb', 'Fw', 'RfTx', 'Semi', 'Batadc']}
    if 'analysis_time' not in st.session_state:
        st.session_state.analysis_time = {k: None for k in ['Pcb', 'Fw', 'RfTx', 'Semi', 'Batadc']}
    if 'field_mapping' not in st.session_state:
        st.session_state.field_mapping = {}

    tabs = st.tabs(["파일 Pcb 분석", "파일 Fw 분석", "파일 RfTx 분석", "파일 Semi 분석", "파일 Batadc 분석"])
    tab_map = {
        'Pcb': {'tab': tabs[0], 'reader': read_csv_with_dynamic_header, 'analyzer': analyze_data, 'jig_col': 'PcbMaxIrPwr', 'timestamp_col': 'PcbStartTime'},
        'Fw': {'tab': tabs[1], 'reader': read_csv_with_dynamic_header_for_Fw, 'analyzer': analyze_Fw_data, 'jig_col': 'FwPC', 'timestamp_col': 'FwStamp'},
        'RfTx': {'tab': tabs[2], 'reader': read_csv_with_dynamic_header_for_RfTx, 'analyzer': analyze_RfTx_data, 'jig_col': 'RfTxPC', 'timestamp_col': 'RfTxStamp'},
        'Semi': {'tab': tabs[3], 'reader': read_csv_with_dynamic_header_for_Semi, 'analyzer': analyze_Semi_data, 'jig_col': 'SemiAssyMaxSolarVolt', 'timestamp_col': 'SemiAssyStartTime'},
        'Batadc': {'tab': tabs[4], 'reader': read_csv_with_dynamic_header_for_Batadc, 'analyzer': analyze_Batadc_data, 'jig_col': 'BatadcPC', 'timestamp_col': 'BatadcStamp'}
    }

    for key, props in tab_map.items():
        with props['tab']:
            st.header(f"{key.upper()} 데이터 분석")
            st.session_state.uploaded_files[key] = st.file_uploader(f"{key.upper()} 파일을 선택하세요", type=["csv"], key=f"uploader_{key}")
            
            if st.session_state.uploaded_files[key]:
                if st.button(f"{key.upper()} 분석 실행", key=f"analyze_{key}"):
                    try:
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
                            
                        # 타임스탬프 변환 로직
                        try:
                            df[props['timestamp_col']] = pd.to_datetime(df[props['timestamp_col']], errors='coerce')
                            if df[props['timestamp_col']].isnull().all():
                                st.warning(f"타임스탬프 변환에 실패했습니다. {props['timestamp_col']} 컬럼의 형식을 확인해주세요.")
                                st.session_state.analysis_results[key] = None
                                continue
                        except Exception as e:
                            st.warning(f"타임스탬프 변환 중 오류가 발생했습니다: {e}")
                            st.session_state.analysis_results[key] = None
                            continue

                        with st.spinner("데이터 분석 및 저장 중..."):
                            st.session_state.analysis_results[key] = df.copy()
                            st.session_state.analysis_data[key] = props['analyzer'](df)
                            st.session_state.analysis_time[key] = datetime.now().strftime('%Y-%m-%d')
                        st.success("분석 완료! 결과가 저장되었습니다.")
                        
                    except Exception as e:
                        st.error(f"분석 중 오류 발생: {e}")
                        st.session_state.analysis_results[key] = None

                if st.session_state.analysis_results[key] is not None:
                    display_analysis_result(key, st.session_state.uploaded_files[key].name, props)

if __name__ == "__main__":
    main()