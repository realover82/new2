import pandas as pd
import numpy as np
import io
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

def clean_string_format(value):
    if isinstance(value, str) and value.startswith('="') and value.endswith('"'):
        return value[2:-1]
    return value

def read_csv_with_dynamic_header(uploaded_file):
    try:
        file_content = io.BytesIO(uploaded_file.getvalue())
        df_temp = pd.read_csv(file_content, header=None, nrows=100, encoding='utf-8')
        
        keywords = ['SNumber', 'PcbStartTime', 'PcbMaxIrPwr', 'PcbPass']
        
        header_row = None
        for i, row in df_temp.iterrows():
            row_values = [str(x).strip() for x in row.values if pd.notna(x)]
            
            if all(keyword in row_values for keyword in keywords):
                header_row = i
                break
        
        if header_row is not None:
            file_content.seek(0)
            df = pd.read_csv(file_content, header=header_row, encoding='utf-8')
            return df
        else:
            return None
    except Exception as e:
        return None

def analyze_data(df):
    for col in df.columns:
        df[col] = df[col].apply(clean_string_format)

    df['PcbStartTime'] = pd.to_datetime(df['PcbStartTime'], errors='coerce')
    df['PassStatusNorm'] = df['PcbPass'].fillna('').astype(str).str.strip().str.upper()

    summary_data = {}
    
    # PcbMaxIrPwr 열이 없는 경우를 대비
    if 'PcbMaxIrPwr' not in df.columns:
        df['PcbMaxIrPwr'] = 'DefaultJig'

    for jig, group in df.groupby('PcbMaxIrPwr'):
        if group['PcbStartTime'].dt.date.dropna().empty:
            continue
        
        for d, day_group in group.groupby(group['PcbStartTime'].dt.date):
            if pd.isna(d):
                continue
            
            date_iso = pd.to_datetime(d).strftime("%Y-%m-%d")

            # 'O'가 하나라도 포함된 SNumber를 'pass'로 간주
            pass_sns_series = day_group.groupby('SNumber')['PassStatusNorm'].apply(lambda x: 'O' in x.tolist())
            pass_sns = pass_sns_series[pass_sns_series].index.tolist()

            # 전체 'O' 개수
            pass_count = (day_group['PassStatusNorm'] == 'O').sum()

            # 가성불량: 'X'이지만, 해당 SNumber가 pass_sns에 포함되는 경우
            false_defect_df = day_group[(day_group['PassStatusNorm'] == 'X') & (day_group['SNumber'].isin(pass_sns))]
            false_defect_count = false_defect_df.shape[0]
            false_defect_sns = false_defect_df['SNumber'].unique().tolist()

            # 진성불량: 'X'이고, 해당 SNumber가 pass_sns에 포함되지 않는 경우
            true_defect_df = day_group[(day_group['PassStatusNorm'] == 'X') & (~day_group['SNumber'].isin(pass_sns))]
            true_defect_count = true_defect_df.shape[0]
            # 수정: 진성불량 상세 목록 추가
            true_defect_sns = true_defect_df['SNumber'].unique().tolist()

            total_test = len(day_group)
            fail_count = false_defect_count + true_defect_count
            
            # 수정: FAIL 상세 목록 추가
            fail_df = day_group[day_group['PassStatusNorm'] == 'X']
            fail_sns = fail_df['SNumber'].unique().tolist()

            rate = 100 * pass_count / total_test if total_test > 0 else 0

            if jig not in summary_data:
                summary_data[jig] = {}
            
            # 수정: 모든 상세 목록을 summary_data에 포함
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
    
    all_dates = sorted(list(df['PcbStartTime'].dt.date.dropna().unique()))
    return summary_data, all_dates