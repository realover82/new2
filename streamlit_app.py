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

def display_analysis_result(analysis_key, file_name, jig_col_name):
    """ session_state에 저장된 분석 결과를 Streamlit에 표시하는 함수 """
    if st.session_state.analysis_results[analysis_key] is None:
        st.error("데이터 로드에 실패했습니다. 파일 형식을 확인해주세요.")
        return

    summary_data, all_dates = st.session_state.analysis_data[analysis_key]
    df_raw = st.session_state.analysis_results[analysis_key]

    st.markdown(f"### '{file_name}' 분석 리포트")

    # --- 기본 필터링 (Jig, 날짜 범위) ---
    st.subheader("기본 필터링")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        jig_list = sorted(df_raw[jig_col_name].dropna().unique().tolist()) if jig_col_name in df_raw.columns else []
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
    for date_obj in all_dates: # 전체 날짜에 대해 집계 데이터 미리 계산
        daily_totals = {key: 0 for key in ['total_test', 'pass', 'false_defect', 'true_defect', 'fail']}
        for jig in jigs_to_display:
            data_point = summary_data.get(jig, {}).get(date_obj.strftime('%Y-%m-%d'))
            if data_point:
                for key in daily_totals:
                    daily_totals[key] += data_point.get(key, 0)
        daily_aggregated_data[date_obj] = daily_totals

    # --- 최종일 데이터 요약 (KPI 카드) ---
    st.subheader(f"요약: {end_date.strftime('%Y-%m-%d')}")
    
    last_day_data = daily_aggregated_data.get(end_date)
    prev_date = end_date - timedelta(days=1)
    prev_day_data = daily_aggregated_data.get(prev_date)

    delta_false, delta_true = None, None
    if last_day_data and prev_day_data:
        delta_false = last_day_data['false_defect'] - prev_day_data['false_defect']
        delta_true = last_day_data['true_defect'] - prev_day_data['true_defect']

    kpi_cols = st.columns(5)
    if last_day_data:
        kpi_cols[0].metric("총 테스트 수", f"{last_day_data['total_test']:,}")
        kpi_cols[1].metric("PASS", f"{last_day_data['pass']:,}")
        kpi_cols[2].metric("FAIL", f"{last_day_data['fail']:,}")
        kpi_cols[3].metric("가성불량", f"{last_day_data['false_defect']:,}", delta=f"{delta_false}" if delta_false is not None else None)
        kpi_cols[4].metric("진성불량", f"{last_day_data['true_defect']:,}", delta=f"{delta_true}" if delta_true is not None else None)
    st.markdown("---")


    # --- 일별 요약 테이블 ---
    st.subheader("일별 요약 테이블")
    report_data = {'지표': ['총 테스트 수', 'PASS', '가성불량', '진성불량', 'FAIL']}
    for date_obj in filtered_dates:
        daily_totals = daily_aggregated_data.get(date_obj, {})
        date_str_col = date_obj.strftime('%y%m%d')
        report_data[date_str_col] = [
            daily_totals.get('total_test', 0), daily_totals.get('pass', 0), daily_totals.get('false_defect', 0),
            daily_totals.get('true_defect', 0), daily_totals.get('fail', 0)
        ]
    report_df = pd.DataFrame(report_data).set_index('지표')
    st.dataframe(report_df)

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
    
    chart_data_list = [
        {'date': date, '가성불량': data['false_defect'], '진성불량': data['true_defect'], 'FAIL': data['fail']}
        for date, data in daily_aggregated_data.items() if start_date <= date <= end_date
    ]

    if chart_data_list:
        chart_df = pd.DataFrame(chart_data_list)
        chart_df_melted = chart_df.melt('date', var_name='불량 유형', value_name='수량')

        common_chart = alt.Chart(chart_df_melted).encode(
            x=alt.X('date:T', axis=alt.Axis(title='날짜')),#, format='%Y-%m-%d')),
            y=alt.Y('수량:Q', axis=alt.Axis(title='불량 건수')),
            color=alt.Color('불량 유형', legend=alt.Legend(title="불량 유형")),
            tooltip=['date:T', '불량 유형', '수량']
        ).properties(title='일자별 불량 건수 추이').interactive()

        if st.session_state[chart_mode_key] == 'line':
            st.altair_chart(common_chart.mark_line(point=True), use_container_width=True)
        else: # 'bar'
            st.altair_chart(common_chart.mark_bar(), use_container_width=True)
    else:
        st.info("그래프를 표시할 데이터가 없습니다.")

    st.markdown("---")

    # --- 상세 내역 (날짜별 펼치기) ---
    st.subheader("상세 내역 (일별)")
    for date_obj in filtered_dates:
        st.markdown(f"**{date_obj.strftime('%Y-%m-%d')}**")
        
        for jig in jigs_to_display:
            data_point = summary_data.get(jig, {}).get(date_obj.strftime('%Y-%m-%d'))
            if not data_point or data_point.get('total_test', 0) == 0:
                continue

            st.markdown(f"**PC(Jig): {jig}**")
            categories = ['pass', 'false_defect', 'true_defect', 'fail']
            labels = ['PASS', '가성불량', '진성불량', 'FAIL']

            for cat, label in zip(categories, labels):
                # 1. 원본 데이터프레임에서 필터링하여 전체 데이터 가져오기
                if cat == 'pass':
                    filtered_df = df_raw[(df_raw[jig_col_name] == jig) & (df_raw['PassStatusNorm'] == 'O')]
                elif cat == 'fail':
                    filtered_df = df_raw[(df_raw[jig_col_name] == jig) & (df_raw['PassStatusNorm'] == 'X')]
                else:
                    # '가성불량'과 '진성불량'은 SNumber 기준으로 필터링
                    if cat == 'false_defect':
                        sn_list = data_point.get(f'{cat}_sns', [])
                        filtered_df = df_raw[df_raw['SNumber'].isin(sn_list)]
                    else: # 'true_defect'
                        sn_list = data_point.get(f'{cat}_sns', [])
                        filtered_df = df_raw[df_raw['SNumber'].isin(sn_list)]

                # 날짜 필터링
                filtered_df = filtered_df[filtered_df[f'{analysis_key}Stamp'].dt.date == date_obj]
                
                if filtered_df.empty:
                    continue

                count = len(filtered_df)
                unique_count = len(filtered_df['SNumber'].unique())

                expander_title = f"{label} - {count}건 (중복값제거 SN: {unique_count}건)"
                
                with st.expander(expander_title, expanded=False):
                    # 2. st.session_state에서 필드 매핑 가져오기
                    fields_to_display = st.session_state.field_mapping.get(analysis_key, ['SNumber'])
                    
                    if not fields_to_display:
                        st.info("표시할 필드가 정의되지 않았습니다.")
                        continue

                    # 3. 데이터프레임을 순회하며 각 필드 출력
                    for _, row in filtered_df.iterrows():
                        formatted_fields = [f"{field}: {row.get(field, 'N/A')}" for field in fields_to_display]
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
# 메인 실행 함수 (기존과 동일)
# ==============================
def main():
    st.set_page_config(layout="wide")
    st.title("리모컨 생산 데이터 분석 툴")
    st.markdown("---")

    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {k: None for k in ['Pcb', 'Fw', 'RfTx', 'Semi', 'Batadc
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {k: None for k in ['Pcb', 'Fw', 'RfTx', 'Semi', 'Batadc
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = {k: None for k in ['Pcb', 'Fw', 'RfTx', 'Semi', 'Batadc
    if 'analysis_time' not in st.session_state:
        st.session_state.analysis_time = {k: None for k in ['Pcb', 'Fw', 'RfTx', 'Semi', 'Batadc

    tabs = st.tabs(["파일 Pcb 분석", "파일 Fw 분석", "파일 RfTx 분석", "파일 Semi 분석", "파일 Batadc"])
    tab_map = {
        'Pcb': {'tab': tabs[0], 'reader': read_csv_with_dynamic_header, 'analyzer': analyze_data, 'jig_col': 'PcbMaxIrPwr'},
        'Fw': {'tab': tabs[1], 'reader': read_csv_with_dynamic_header_for_Fw, 'analyzer': analyze_Fw_data, 'jig_col': 'FwPC'},
        'RfTx': {'tab': tabs[2], 'reader': read_csv_with_dynamic_header_for_RfTx, 'analyzer': analyze_RfTx_data, 'jig_col': 'RfTxPC'},
        'Semi': {'tab': tabs[3], 'reader': read_csv_with_dynamic_header_for_Semi, 'analyzer': analyze_Semi_data, 'jig_col': 'SemiAssyMaxSolarVolt'},
        'Batadc': {'tab': tabs[4], 'reader': read_csv_with_dynamic_header_for_Batadc, 'analyzer': analyze_Batadc_data, 'jig_col': 'BatadcPC'}
    }

    for key, props in tab_map.items():
        with props['tab']:
            st.header(f"{key.upper()} 데이터 분석")
            st.session_state.uploaded_files[key] = st.file_uploader(f"{key.upper()} 파일을 선택하세요", type=["csv"], key=f"uploader_{key}")
            
            if st.session_state.uploaded_files[key]:
                if st.button(f"{key.upper()} 분석 실행", key=f"analyze_{key}"):
                    try:
                        df = props['reader'](st.session_state.uploaded_files[key])
                        if df is not None:
                            with st.spinner("데이터 분석 및 저장 중..."):
                                st.session_state.analysis_results[key] = df
                                st.session_state.analysis_data[key] = props['analyzer'](df)
                                st.session_state.analysis_time[key] = datetime.now().strftime('%Y-%m-%d') # %H:%M:%S')
                            st.success("분석 완료! 결과가 저장되었습니다.")
                        else:
                            st.error(f"{key.upper()} 데이터 파일을 읽을 수 없습니다. 파일 형식을 확인해주세요.")
                    except Exception as e:
                        st.error(f"분석 중 오류 발생: {e}")

                if st.session_state.analysis_results[key] is not None:
                    display_analysis_result(key, st.session_state.uploaded_files[key].name, props['jig_col'])

if __name__ == "__main__":
    main()