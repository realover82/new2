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
                # 전체 파일을 header=None으로 먼저 읽어와서 헤더 위치를 찾습니다.
                df_temp = pd.read_csv(file_content, header=None, encoding=encoding, na_filter=False, skipinitialspace=True)
                
                keywords = ['snumber', 'pcbstarttime', 'pcbmaxirpwr', 'pcbpass', 'pcbsleepcurr']
                
                header_row = None
                for i, row in df_temp.iterrows():
                    # 모든 값을 소문자로 변환하고 양쪽 공백 제거
                    row_values_lower = [str(x).strip().lower() for x in row.values]
                    if all(keyword in row_values_lower for keyword in keywords):
                        header_row = i
                        break
                
                if header_row is not None:
                    file_content.seek(0)
                    df = pd.read_csv(file_content, header=header_row, encoding=encoding, dtype=str, skipinitialspace=True)
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

    # === PassStatusNorm 컬럼 생성 (최우선) ===
    pass_col = 'PcbPass'
    try:
        pass_col_actual = next(col for col in df.columns if col.strip().lower() == pass_col.lower())
        df['PassStatusNorm'] = df[pass_col_actual].fillna('').astype(str).str.strip().str.upper()
    except StopIteration:
        st.error(f"'{pass_col}' 컬럼을 찾을 수 없어 'PassStatusNorm' 생성에 실패했습니다.")
        return None, None
    # =========================================================================

    # 타임스탬프 컬럼 이름 찾기
    timestamp_col = 'PcbStartTime'
    try:
        timestamp_col_actual = next(col for col in df.columns if col.strip().lower() == timestamp_col.lower())
    except StopIteration:
        st.error(f"'{timestamp_col}' 컬럼이 데이터에 없습니다.")
        return None, None

    # === 수정된 타임스탬프 변환 로직 ===
    
    # 1. YYYYMMDDHHmmss 형식 변환 시도 (문자열 전용)
    df['temp_converted'] = pd.to_datetime(df[timestamp_col_actual].astype(str).str.strip(), format='%Y%m%d%H%M%S', errors='coerce')

    # 2. 유닉스 타임스탬프 (초 단위) 변환 시도
    numeric_series = pd.to_numeric(df[timestamp_col_actual].astype(str).str.strip(), errors='coerce')
    
    # 초 단위로 변환한 결과를 임시 컬럼에 저장
    seconds_converted = pd.to_datetime(numeric_series, unit='s', errors='coerce')
    
    # 3. 유닉스 타임스탬프 (밀리초 단위) 변환 시도
    milliseconds_converted = pd.to_datetime(numeric_series, unit='ms', errors='coerce')
    
    # 최종 변환 결과 선택 및 병합
    
    # 3-1. 14자리 문자열 변환 결과가 유효하면 사용
    final_series = df['temp_converted'].copy()
    
    # 3-2. 문자열 변환에 실패한 NaN 값들에 대해 초 단위 변환 결과(최근 날짜) 사용
    is_na = final_series.isnull()
    
    # seconds_converted 중 1980년 이후의 날짜만 유효한 것으로 간주하여 1970년 에러 방지
    is_valid_seconds = seconds_converted.notnull() & (seconds_converted.dt.year > 1980) 
    final_series[is_na & is_valid_seconds] = seconds_converted[is_na & is_valid_seconds]
    is_na = final_series.isnull()

    # 3-3. 초 단위 변환에도 실패한 NaN 값들에 대해 밀리초 단위 변환 결과 사용
    final_series[is_na] = milliseconds_converted[is_na]
    
    # 임시 컬럼 제거 및 최종 업데이트
    df = df.drop(columns=['temp_converted'], errors='ignore')
    
    # 최종 결과 확인 및 컬럼 업데이트
    if final_series.isnull().all():
        st.warning(f"타임스탬프 변환에 실패했습니다. '{timestamp_col_actual}' 컬럼의 형식을 확인해주세요.")
        return None, None
        
    df[timestamp_col_actual] = final_series
    # ======================================
    
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