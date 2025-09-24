import pandas as pd
import numpy as np
import io
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

def clean_string_format(value):
    """다양한 형태의 문자열 포맷을 정리하는 함수"""
    if pd.isna(value):
        return value
    
    value_str = str(value).strip()
    
    if value_str.startswith('="') and value_str.endswith('"'):
        return value_str[2:-1]
    
    if value_str.startswith('""') and value_str.endswith('""'):
        return value_str[2:-2]
    
    if value_str.startswith('"') and value_str.endswith('"') and len(value_str) > 2:
        return value_str[1:-1]
    
    return value_str

def read_csv_with_dynamic_header_for_Semi(uploaded_file):
    """SemiAssy 데이터에 맞는 키워드로 헤더를 찾아 DataFrame을 로드하는 함수"""
    try:
        encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin-1']
        
        for encoding in encodings:
            try:
                file_content = io.BytesIO(uploaded_file.getvalue())
                df_temp = pd.read_csv(file_content, header=None, nrows=20, encoding=encoding, skipinitialspace=True)
                
                keywords = ['SNumber', 'SemiAssyStartTime', 'SemiAssyPass'] # 필수 키워드만 확인
                
                header_row = None
                for i, row in df_temp.iterrows():
                    row_values = [str(x).strip() for x in row.values if pd.notna(x) and str(x).strip() != '']
                    
                    matched_keywords = sum(1 for kw in keywords if any(kw in str(val) for val in row_values))
                    
                    if matched_keywords >= len(keywords):
                        header_row = i
                        break
                
                if header_row is not None:
                    file_content.seek(0)
                    df = pd.read_csv(file_content, header=header_row, encoding=encoding, skipinitialspace=True)
                    df.columns = df.columns.str.strip()
                    
                    if df.columns[0] == '' or pd.isna(df.columns[0]) or str(df.columns[0]).strip() == '':
                        df = df.iloc[:, 1:].copy()
                    
                    return df
                
            except Exception:
                continue
        
        return None
            
    except Exception:
        return None

def analyze_Semi_data(df):
    """SemiAssy 데이터의 분석 로직을 담고 있는 함수"""
    try:
        required_columns = ['SNumber', 'SemiAssyStartTime', 'SemiAssyMaxSolarVolt', 'SemiAssyPass']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"필수 컬럼이 없습니다: {missing_columns}")
        
        for col in df.columns:
            df[col] = df[col].apply(clean_string_format)

        df['SemiAssyStartTime'] = pd.to_datetime(df['SemiAssyStartTime'], format='%Y%m%d%H%M%S', errors='coerce')
        df['PassStatusNorm'] = df['SemiAssyPass'].fillna('').astype(str).str.strip().str.upper()

        df_valid = df.dropna(subset=['SemiAssyStartTime']).copy()
        
        if df_valid.empty:
            raise ValueError("유효한 날짜 데이터가 없습니다.")

        # ★★★ 에러 해결을 위한 핵심 로직 ★★★
        # Jig로 사용할 컬럼을 동적으로 찾습니다. 없으면 기본값을 사용합니다.
        if 'SemiAssyMaxSolarVolt' in df_valid.columns and not df_valid['SemiAssyMaxSolarVolt'].isna().all():
            jig_column = 'SemiAssyMaxSolarVolt'
        elif 'BatadcPC' in df_valid.columns and not df_valid['BatadcPC'].isna().all():
            jig_column = 'BatadcPC'
        else:
            df_valid['DEFAULT_JIG'] = 'SemiAssy_JIG'
            jig_column = 'DEFAULT_JIG'
        
        summary_data = {}
        
        for jig, group in df_valid.groupby(jig_column):
            if pd.isna(jig) or str(jig).strip() == '':
                continue
            
            for d, day_group in group.groupby(group['SemiAssyStartTime'].dt.date):
                if pd.isna(d):
                    continue
                
                date_iso = pd.to_datetime(d).strftime("%Y-%m-%d")
                
                ever_passed_sns = day_group[day_group['PassStatusNorm'] == 'O']['SNumber'].unique()

                pass_df = day_group[day_group['PassStatusNorm'] == 'O']
                fail_df = day_group[day_group['PassStatusNorm'] == 'X']
                false_defect_df = fail_df[fail_df['SNumber'].isin(ever_passed_sns)]
                true_defect_df = fail_df[~fail_df['SNumber'].isin(ever_passed_sns)]

                pass_sns = pass_df['SNumber'].unique().tolist()
                false_defect_sns = false_defect_df['SNumber'].unique().tolist()
                true_defect_sns = true_defect_df['SNumber'].unique().tolist()
                fail_sns = fail_df['SNumber'].unique().tolist()
                
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

                    'pass_sns': pass_sns, 
                    'false_defect_sns': false_defect_sns,
                    'true_defect_sns': true_defect_sns, 
                    'fail_sns': fail_sns,
                    
                    'pass_unique_count': len(pass_sns),
                    'false_defect_unique_count': len(false_defect_sns),
                    'true_defect_unique_count': len(true_defect_sns),
                    'fail_unique_count': len(fail_sns)
                }
        
        all_dates = sorted(list(df_valid['SemiAssyStartTime'].dt.date.dropna().unique()))
        return summary_data, all_dates
    except Exception as e:
        # Streamlit에 더 친절한 에러 메시지를 전달합니다.
        st.error(f"Semi 데이터 분석 중 오류가 발생했습니다: {e}")
        return None, []