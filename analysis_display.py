import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
from typing import Dict, Any, List

# config 파일에서 분석 키 속성(jig_col, timestamp_col)을 가져올 수 있도록 합니다.
# 실제 config.py 파일이 같은 경로에 있다고 가정합니다.
from config import TAB_PROPS_MAP

def display_analysis_result(analysis_key: str, file_name: str, props: Dict[str, str]):
    """ session_state에 저장된 분석 결과를 Streamlit에 표시하는 함수 """
    
    # 세션 상태에서 데이터 가져오기
    if st.session_state.analysis_results.get(analysis_key) is None:
        st.error("데이터 로드에 실패했습니다. 파일 형식을 확인해주세요.")
        return

    if st.session_state.analysis_data.get(analysis_key) is None:
        st.error("데이터 분석에 실패했습니다. 분석 함수를 확인해주세요.")
        return
        
    summary_data, all_dates = st.session_state.analysis_data[analysis_key]
    df_raw = st.session_state.analysis_results[analysis_key]
    
    # all_dates가 None일 경우 처리
    if all_dates is None:
        st.error("데이터 분석에 실패했습니다. 날짜 관련 컬럼 형식을 확인해주세요.")
        return
    # =======================================================
    
    st.markdown(f"### '{file_name}' 분석 리포트")

    # === 필수 컬럼 존재 여부 확인 ===
    required_columns = [props['jig_col'], props['timestamp_col']]
    missing_columns = [col for col in required_columns if col not in df_raw.columns]
    
    if missing_columns:
        st.error(f"데이터에 필수 컬럼이 없습니다: {', '.join(missing_columns)}. 파일을 다시 확인해주세요.")
        return
    # =======================================================
    
    # --- 기본 필터링 (Jig, 날짜 범위) ---
    st.subheader("기본 필터링")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    if props['jig_col'] in df_raw.columns:
        jig_list = sorted(df_raw[props['jig_col']].dropna().unique().tolist())
    else:
        jig_list = []

    with filter_col1:
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

    # --- 데이터 집계 (선택된 Jig 및 날짜 범위에 따른 일별 집계) ---
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
        summary_df_data = {
            '날짜': [d.strftime('%m-%d') for d in filtered_dates],
            '총 테스트 수': [daily_aggregated_data.get(d, {}).get('total_test', 0) for d in filtered_dates],
            'PASS': [daily_aggregated_data.get(d, {}).get('pass', 0) for d in filtered_dates],
            '가성불량': [daily_aggregated_data.get(d, {}).get('false_defect', 0) for d in filtered_dates],
            '진성불량': [daily_aggregated_data.get(d, {}).get('true_defect', 0) for d in filtered_dates],
            'FAIL': [daily_aggregated_data.get(d, {}).get('fail', 0) for d in filtered_dates]
        }
        summary_df = pd.DataFrame(summary_df_data).set_index('날짜')
        st.dataframe(summary_df.transpose())
    else:
        st.info("선택된 조건에 해당하는 요약 데이터가 없습니다.")

    st.markdown("---")
    
    # --- 상세 내역 (일별) ---
    st.subheader("상세 내역 (일별)")
    
    # 1. 상세 내역 필드 선택 기능 추가
    all_raw_columns = df_raw.columns.tolist()
    
    # 디폴트 필드 구성: SNumber와 모든 QC 컬럼으로만 제한
    snumber_col = next((col for col in all_raw_columns if col.lower() == 'snumber'), 'SNumber')
    qc_cols_found = [col for col in all_raw_columns if col.endswith('_QC')]
    initial_default = list(set([snumber_col] + qc_cols_found)) 
    
    selected_detail_fields = st.multiselect(
        "상세 내역에 표시할 필드 선택",
        all_raw_columns,
        default=initial_default,
        key=f"detail_fields_select_{analysis_key}"
    )
    
    # 2. 상세 내역 보기 제어용 세션 상태 변수 초기화 및 버튼
    if f'show_details_{analysis_key}' not in st.session_state:
        st.session_state[f'show_details_{analysis_key}'] = False

    if st.button("상세 내역 조회", key=f"show_details_btn_{analysis_key}"):
        st.session_state[f'show_details_{analysis_key}'] = True
        st.session_state[f'detail_mode_{analysis_key}'] = 'defects' # 기본값: 불량만 보기
        st.session_state[f'qc_filter_mode_{analysis_key}'] = 'None' # 필터 모드 초기화


    if st.session_state[f'show_details_{analysis_key}']:
        if f'detail_mode_{analysis_key}' not in st.session_state:
            st.session_state[f'detail_mode_{analysis_key}'] = 'all'

        detail_col1, detail_col2, detail_col3, detail_col4, detail_col5 = st.columns(5) # 5개의 컬럼으로 확장
        
        with detail_col1:
            if st.button("전체 보기", key=f"detail_all_{analysis_key}"):
                st.session_state[f'detail_mode_{analysis_key}'] = 'all'
                st.session_state[f'qc_filter_mode_{analysis_key}'] = 'None' 
        with detail_col2:
            if st.button("불량만 보기", key=f"detail_defects_{analysis_key}"):
                st.session_state[f'detail_mode_{analysis_key}'] = 'defects'
                st.session_state[f'qc_filter_mode_{analysis_key}'] = 'None'
        with detail_col3:
            if st.button("PASS만 보기", key=f"detail_pass_{analysis_key}"):
                st.session_state[f'detail_mode_{analysis_key}'] = 'pass'
                st.session_state[f'qc_filter_mode_{analysis_key}'] = 'None'
                
        # === 새로운 필터 버튼 추가 (QC 상태 필터링) ===
        with detail_col4:
            if st.button("불량(초과,미달만)", key=f"filter_qc_fail_{analysis_key}"):
                st.session_state[f'qc_filter_mode_{analysis_key}'] = 'FailOnly'
                st.session_state[f'detail_mode_{analysis_key}'] = 'all' # 전체 모드에서 필터링
        with detail_col5:
            if st.button("PASS(미달/초과 포함)", key=f"filter_qc_pass_{analysis_key}"): # PASS 항목 중 미달/초과된 항목만 보기
                st.session_state[f'qc_filter_mode_{analysis_key}'] = 'PassOnly'
                st.session_state[f'detail_mode_{analysis_key}'] = 'all' # 전체 모드에서 필터링
        # ============================================= 
        
        current_mode = st.session_state[f'detail_mode_{analysis_key}']
        qc_filter_mode = st.session_state[f'qc_filter_mode_{analysis_key}']
        
        for date_obj in filtered_dates:
            st.markdown(f"**{date_obj.strftime('%Y-%m-%d')}**")
            
            for jig in jigs_to_display:
                data_point = summary_data.get(jig, {}).get(date_obj.strftime('%Y-%m-%d'))
                if not data_point or data_point.get('total_test', 0) == 0:
                    continue

                st.markdown(f"**PC(Jig): {jig}**")
                
                # === 1. 카테고리 결정 로직 ===
                if qc_filter_mode == 'FailOnly':
                    categories = ['false_defect', 'true_defect'] 
                    labels = ['가성불량', '진성불량']
                elif qc_filter_mode == 'PassOnly':
                    categories = ['pass'] # PASS 카테고리 데이터만 가져옵니다.
                    labels = ['PASS']
                elif current_mode == 'defects':
                    categories = ['false_defect', 'true_defect']
                    labels = ['가성불량', '진성불량']
                elif current_mode == 'pass':
                    categories = ['pass']
                    labels = ['PASS']
                else: 
                    categories = ['pass', 'false_defect', 'true_defect', 'fail']
                    labels = ['PASS', '가성불량', '진성불량', 'FAIL']

                # ============================================================

                for cat, label in zip(categories, labels):
                    full_data_list = data_point.get(f'{cat}_data', [])
                    
                    if not full_data_list:
                        continue
                    
                    # === 2. QC 필터링 로직 (각 카테고리별로 필터링) ===
                    is_qc_filtering_active = qc_filter_mode in ['FailOnly', 'PassOnly']

                    if is_qc_filtering_active:
                        selected_qc_cols_for_filter = [col for col in selected_detail_fields if col.endswith('_QC')]
                        
                        if selected_qc_cols_for_filter:
                            filtered_list = []
                            target_statuses = ['미달', '초과']
                            
                            for record in full_data_list:
                                qc_value_found = False
                                for qc_col in selected_qc_cols_for_filter:
                                    qc_value = record.get(qc_col)
                                    
                                    # 조건 1: '불량(초과,미달만)' 버튼을 눌렀을 경우
                                    if qc_filter_mode == 'FailOnly' and qc_value in target_statuses:
                                        qc_value_found = True
                                        break
                                    # 조건 2: 'PASS(미달/초과 포함)' 버튼을 눌렀을 경우
                                    elif qc_filter_mode == 'PassOnly' and cat == 'pass' and qc_value in target_statuses:
                                        # PASS 카테고리 AND QC 미달/초과인 경우만 필터링
                                        qc_value_found = True
                                        break
                                    
                                if qc_value_found:
                                    filtered_list.append(record)
                            
                            full_data_list = filtered_list # 필터링된 리스트로 교체

                    if not full_data_list:
                        continue
                    # ======================================================

                    count = len(full_data_list)
                    unique_count = len(set(d.get('SNumber', 'N/A') for d in full_data_list))

                    fields_to_check = selected_detail_fields
                    selected_qc_cols = [col for col in fields_to_check if col.endswith('_QC')]
                    
                    qc_summary_parts_html = []
                    qc_summary_parts_plain = [] 

                    for qc_col in selected_qc_cols:
                        qc_statuses = [record.get(qc_col) for record in full_data_list if record.get(qc_col) is not None]
                        
                        if not qc_statuses:
                            continue
                            
                        qc_counts = pd.Series(qc_statuses).value_counts().to_dict()
                        
                        parts_html = []
                        parts_plain = []
                        
                        # --- HTML 및 Plain Text 구성 로직 ---
                        # Pass, 제외, 데이터 부족 (기본색 / Plain Text)
                        if qc_counts.get('Pass', 0) > 0:
                            parts_html.append(f"Pass {qc_counts['Pass']}건")
                            parts_plain.append(f"Pass {qc_counts['Pass']}건")
                        if qc_counts.get('제외', 0) > 0:
                            parts_html.append(f"제외 {qc_counts['제외']}건")
                            parts_plain.append(f"제외 {qc_counts['제외']}건")
                        if qc_counts.get('데이터 부족', 0) > 0:
                            parts_html.append(f"데이터 부족 {qc_counts['데이터 부족']}건")
                            parts_plain.append(f"데이터 부족 {qc_counts['데이터 부족']}건")
                            
                        # 미달/초과 (빨간색 적용)
                        if qc_counts.get('미달', 0) > 0:
                            parts_html.append(f"<span style='color:red;'>미달 {qc_counts['미달']}건</span>")
                            parts_plain.append(f"미달 {qc_counts['미달']}건")
                        if qc_counts.get('초과', 0) > 0:
                            parts_html.append(f"<span style='color:red;'>초과 {qc_counts['초과']}건</span>")
                            parts_plain.append(f"초과 {qc_counts['초과']}건")
                        
                        if parts_plain: # 순수 텍스트가 있어야만 집계함
                            qc_summary_parts_html.append(f"**{qc_col.replace('_QC', '')}**: {', '.join(parts_html)}")
                            qc_summary_parts_plain.append(f"{qc_col.replace('_QC', '')}: {', '.join(parts_plain)}")
                        # --- HTML 및 Plain Text 구성 로직 끝 ---

                    # 1. 제목에 들어갈 순수한 텍스트 QC 요약 구성
                    qc_summary_plain_text = ""
                    if qc_summary_parts_plain:
                        qc_summary_plain_text = f" [QC: {', '.join(qc_summary_parts_plain)}]" 
                        
                    # 2. Expander 제목 구성 (순수 텍스트)
                    expander_title_base = f"{label} - {count}건 (중복값제거 SN: {unique_count}건){qc_summary_plain_text}"
                    
                    with st.expander(expander_title_base, expanded=False):
                        
                        # 3. 제목 아래에 색상이 적용된 QC 요약 정보 출력 (HTML)
                        if qc_summary_parts_html:
                            qc_summary_html_output = f" [<span style='color:black;'>QC: {', '.join(qc_summary_parts_html)}</span>]"
                            qc_html = f"<div>{qc_summary_html_output.replace('QC:', 'QC:')}</div>"
                            st.markdown(qc_html, unsafe_allow_html=True)
                            st.markdown("---")
                        
                        fields_to_display = selected_detail_fields 
                        
                        if not fields_to_display:
                            st.info("표시할 필드가 선택되지 않았습니다.")
                            continue

                        # 4. 상세 내역 개별 항목 출력 (미달/초과 빨간색 적용)
                        for item in full_data_list:
                            formatted_fields = []
                            for field in fields_to_display:
                                value = item.get(field, 'N/A')
                                
                                # === 개별 항목 빨간색 적용 로직 ===
                                if field.endswith('_QC') and value in ['미달', '초과']:
                                    # QC 결과가 '미달' 또는 '초과'일 때 빨간색으로 감쌉니다.
                                    formatted_fields.append(f"{field}: <span style='color:red;'>{value}</span>")
                                else:
                                    formatted_fields.append(f"{field}: {value}")
                                # ===================================
                                
                            # st.markdown을 사용하여 HTML이 렌더링되도록 합니다.
                            st.markdown(", ".join(formatted_fields), unsafe_allow_html=True)

            st.markdown("---")

    # --- DF 조회 기능 ---
    st.subheader("DF 조회")
    search_col1, search_col2, search_col3 = st.columns([1, 2, 1])
    
    with search_col1:
        snumber_query = st.text_input("SNumber 검색", key=f"snumber_search_{analysis_key}")
    with search_col2:
        all_columns = df_raw.columns.tolist()
        qc_cols_default = [col for col in all_columns if col.endswith('_QC')]
        default_cols_for_search = ['SNumber', props['timestamp_col'], 'PassStatusNorm'] + qc_cols_default
        
        selected_columns = st.multiselect(
            "표시할 필드(열) 선택", 
            all_columns, 
            key=f"col_select_{analysis_key}",
            default=[col for col in all_columns if col in default_cols_for_search]
        )
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
    
    # 필터 버튼을 누르지 않았을 경우에도 상태를 유지하기 위해 session_state에서 값을 가져옵니다.
    applied_filters = st.session_state.get(filter_state_key, {'snumber': '', 'columns': []})

    with st.expander("DF 조회"):
        df_display = df_raw.copy()
        
        has_snumber_query = False
        
        if applied_filters['snumber']:
            query = applied_filters['snumber']
            has_snumber_query = True
            
            if 'SNumber' in df_display.columns and pd.api.types.is_string_dtype(df_display['SNumber']):
                # SNumber 컬럼이 문자열이고, 검색어를 포함하는 행 필터링
                df_display = df_display[df_display['SNumber'].str.contains(query, na=False, case=False)]
            else:
                try:
                    # SNumber 컬럼이 없거나 문자열이 아닐 경우, 전체 행에 대해 검색
                    df_display = df_display[df_display.apply(lambda row: query.lower() in str(row.values).lower(), axis=1)]
                except Exception:
                    st.warning("SNumber 검색을 지원하지 않는 데이터 형식입니다.")
                    pass 

        if applied_filters['columns']:
            existing_cols = [col for col in applied_filters['columns'] if col in df_display.columns]
            df_display = df_display[existing_cols]
        
        # 결과 출력
        if df_display.empty:
            if has_snumber_query:
                st.info(f"선택된 필터 조건 ('{applied_filters['snumber']}')에 해당하는 결과가 없습니다. 검색어를 확인하거나 필터를 해제해 주세요.")
            else:
                st.info("데이터프레임에 표시할 행이 없습니다. 분석 데이터(df_raw)를 확인해주세요.")
        else:
            st.dataframe(df_display)
