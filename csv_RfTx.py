import pandas as pd
import numpy as np
import io
from datetime import datetime
import warnings
import streamlit as st

warnings.filterwarnings('ignore')

# '="...' 형식의 문자열을 정리하는 함수
def clean_string_format(value):
    if isinstance(value, str) and value.startswith('="') and value.endswith('"'):
        return value[2:-1]
    return value

def analyze_RfTx_data(df):
    """RfTx 데이터의 분석 로직을 담고 있는 함수"""
    # 데이터 전처리
    for col in df.columns:
        df[col] = df[col].apply(clean_string_format)

    df['RfTxStamp'] = pd.to_datetime(df['RfTxStamp'], errors='coerce')
    df['PassStatusNorm'] = df['RfTxPass'].fillna('').astype(str).str.strip().str.upper()

    summary_data = {}
    
    if 'RfTxPC' not in df.columns:
        df['RfTxPC'] = 'DefaultJig'

    # 1. 모든 Jig에 대해 PASS 기록이 있는 SNumber를 미리 계산합니다.
    #    이렇게 하면 데이터 분석 과정에서 Jig별로 PASS 기록을 효율적으로 확인할 수 있습니다.
    jig_pass_history = df[df['PassStatusNorm'] == 'O'].groupby('RfTxPC')['SNumber'].unique().apply(set).to_dict()

    for jig, group in df.groupby('RfTxPC'):
        # 유효한 날짜 데이터가 없는 그룹은 건너뜁니다.
        group = group.dropna(subset=['RfTxStamp'])
        if group.empty:
            continue
        
        for d, day_group in group.groupby(group['RfTxStamp'].dt.date):
            if pd.isna(d):
                continue
            
            date_iso = pd.to_datetime(d).strftime("%Y-%m-%d")

            # 2. 현재 Jig의 PASS SNumber 집합을 가져옵니다.
            current_jig_passed_sns = jig_pass_history.get(jig, set())
            
            # 각 카테고리별 데이터프레임 필터링
            pass_df = day_group[day_group['PassStatusNorm'] == 'O']
            fail_df = day_group[day_group['PassStatusNorm'] == 'X']
            
            # 3. 가성불량: 현재 Jig에서 FAIL이면서, 동일한 Jig에서 PASS를 기록했던 SNumber
            false_defect_df = fail_df[fail_df['SNumber'].isin(current_jig_passed_sns)]
            
            # 4. 진성불량: 현재 Jig에서 FAIL이지만, 동일한 Jig에서 PASS를 기록한 적이 없는 SNumber
            true_defect_df = fail_df[~fail_df['SNumber'].isin(current_jig_passed_sns)]

            # 각 카테고리별 상세 목록 (고유 SN) 생성
            pass_sns = pass_df['SNumber'].unique().tolist()
            false_defect_sns = false_defect_df['SNumber'].unique().tolist()
            true_defect_sns = true_defect_df['SNumber'].unique().tolist()
            fail_sns = fail_df['SNumber'].unique().tolist()

            # 각 항목별 건수 (테스트 횟수)
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
    
    all_dates = sorted(list(df['RfTxStamp'].dt.date.dropna().unique()))
    return summary_data, all_dates