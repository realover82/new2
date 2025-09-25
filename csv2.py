# csv2.py

import pandas as pd
import numpy as np
import io
from datetime import datetime
import warnings
import streamlit as st

warnings.filterwarnings('ignore')

def clean_string_format(value):
    """'="...' 형식의 문자열을 정리하는 함수"""
    if isinstance(value, str) and value.startswith('="') and value.endswith('"'):
        return value[2:-1]
    return value

def read_csv_with_dynamic_header(uploaded_file):
    """
    PCB 데이터에 맞는 키워드로 헤더를 찾아 DataFrame을 로드하는 함수.
    헤더를 찾기 위해 파일 전체를 읽고, 대소문자 및 공백을 무시합니다.
    """
    try:
        file_content = io.BytesIO(uploaded_file.getvalue())
        encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin1']
        df = None
        for encoding in encodings:
            try:
                file_content.seek(0)
                df_temp = pd.read_csv(file_content, header=None, encoding=encoding, na_filter=False)
                
                keywords = ['snumber', 'pcbstarttime', 'pcbmaxirpwr', 'pcbpass', 'pcbsleepcurr']
                
                header_row = None
                for i, row in df_temp.iterrows():
                    row_values_lower = [str(x).strip().lower() for x in row.values]
                    if all(keyword in row_values_lower for keyword in keywords):
                        header_row = i
                        break
                
                if header_row is not None:
                    file_content.seek(0)
                    df = pd.read_csv(file_content, header=header_row, encoding=encoding)
                    st.sidebar.markdown("---")
                    st.sidebar.subheader("찾은 컬럼 목록")
                    st.sidebar.write(df.columns.tolist())
                    
                    return df
            except Exception:
                continue
        st.error("파일 헤더를 찾을 수 없습니다. 필수 컬럼이 누락되었거나 형식이 다릅니다.")
        return None
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return None

def analyze_data(df):
    """
    PCB 데이터의 분석 로직을 담고 있는 함수.
    PcbStartTime 컬럼의 다양한 타임스탬프 형식을 처리하도록 보강되었습니다.
    """
    # 데이터 전처리
    for col in df.columns:
        df[col] = df[col].apply(clean_string_format)

    # 타임스탬프 컬럼 이름 찾기
    timestamp_col = 'PcbStartTime'
    try:
        timestamp_col_actual = next(col for col in df.columns if col.strip().lower() == timestamp_col.lower())
    except StopIteration:
        st.error(f"'{timestamp_col}' 컬럼이 데이터에 없습니다.")
        return None, None

    # === 수정된 타임스탬프 변환 로직 ===
    converted_series = None
    
    # 1. 밀리초(ms) 단위 변환 시도 (문자열인 경우 숫자로 변환 후 시도)
    try:
        series_to_convert = pd.to_numeric(df[timestamp_col_actual], errors='coerce')
        converted_series = pd.to_datetime(series_to_convert, unit='ms', errors='coerce')
    except Exception:
        pass
    
    # 2. 초(s) 단위 변환 시도
    if converted_series is None or converted_series.isnull().all():
        try:
            series_to_convert = pd.to_numeric(df[timestamp_col_actual], errors='coerce')
            converted_series = pd.to_datetime(series_to_convert, unit='s', errors='coerce')
        except Exception:
            pass
            
    # 3. 다양한 문자열 형식 변환 시도
    if converted_series is None or converted_series.isnull().all():
        try:
            converted_series = pd.to_datetime(df[timestamp_col_actual], errors='coerce')
        except Exception:
            pass

    if converted_series is not None and not converted_series.isnull().all():
        df[timestamp_col_actual] = converted_series
    else:
        st.warning(f"타임스탬프 변환에 실패했습니다. '{timestamp_col_actual}' 컬럼의 형식을 확인해주세요.")
        return None, None
    # ======================================
    
    df['PassStatusNorm'] = df['PcbPass'].fillna('').astype(str).str.strip().str.upper()

    summary_data = {}
    
    jig_col = 'PcbMaxIrPwr'
    if jig_col not in df.columns:
        df[jig_col] = 'DefaultJig'

    jig_pass_history = df[df['PassStatusNorm'] == 'O'].groupby(jig_col)['SNumber'].unique().apply(set).to_dict()

    for jig, group in df.groupby(jig_col):
        group = group.dropna(subset=[timestamp_col_actual])
        if group.empty:
            continue
        
        for d, day_group in group.groupby(group[timestamp_col_actual].dt.date):
            if pd.isna(d):
                continue
            
            date_iso = pd.to_datetime(d).strftime("%Y-%m-%d")
            current_jig_passed_sns = jig_pass_history.get(jig, set())
            
            pass_df = day_group[day_group['PassStatusNorm'] == 'O']
            fail_df = day_group[day_group['PassStatusNorm'] == 'X']
            
            false_defect_df = fail_df[fail_df['SNumber'].isin(current_jig_passed_sns)]
            true_defect_df = fail_df[~fail_df['SNumber'].isin(current_jig_passed_sns)]
            
            pass_count = len(pass_df)
            false_defect_count = len(false_defect_df)
            true_defect_count = len(true_defect_df)
            fail_count = len(fail_df)
            total_test = len(day_group)
            rate = 100 * pass_count / total_test if total_test > 0 else 0

            if jig not in summary_data:
                summary_data[jig] = {}
            
            summary_data[jig][date_iso] = {
                'total_test': total_test,
                'pass': pass_count,
                'false_defect': false_defect_count,
                'true_defect': true_defect_count,
                'fail': fail_count,
                'pass_rate': f"{rate:.1f}%",
                
                'pass_data': pass_df.to_dict('records'),
                'false_defect_data': false_defect_df.to_dict('records'),
                'true_defect_data': true_defect_df.to_dict('records'),
                'fail_data': fail_df.to_dict('records'),

                'pass_unique_count': len(pass_df['SNumber'].unique()),
                'false_defect_unique_count': len(false_defect_df['SNumber'].unique()),
                'true_defect_unique_count': len(true_defect_df['SNumber'].unique()),
                'fail_unique_count': len(fail_df['SNumber'].unique())
            }
    
    all_dates = sorted(list(df[timestamp_col_actual].dt.date.dropna().unique()))
    return summary_data, all_dates