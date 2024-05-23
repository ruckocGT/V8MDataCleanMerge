import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date
import numpy as np

# Script A components
def data_cleanse(df):
    cols_to_check = [0, 1, 2, 4, 5, 6, 7, 8, 9]
    for col in cols_to_check:
        for i in range(1, len(df)):
            if pd.isna(df.iat[i, col]):
                df.iat[i, col] = df.iat[i-1, col]
    return df

def run_script_a():
    st.title("Valid8ME Data Cleanse")
    
    uploaded_file = st.file_uploader("Upload Valid8Me Output for Cleaning", type=['xlsx'])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        
        st.write("Before cleaning:")
        st.write(df.head(20))
        
        if st.button("Clean Data"):
            cleaned_df = data_cleanse(df)
            
            st.write("After cleaning:")
            st.write(cleaned_df.head(20))
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                cleaned_df.to_excel(writer, index=False, sheet_name='Sheet1')
            output.seek(0)
            
            st.download_button(label="Download Cleaned Excel", data=output, file_name="Valid8MeOutput-clean.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            return cleaned_df
    return None

# Script B components
def fill_missing_values(df):
    for col in ['Form template', 'Form template version', 'Request Type', 'Risk Level', 'Audit Opinion']:
        if f'{col}_x' in df.columns and f'{col}_y' in df.columns:
            df[f'{col}_x'].fillna(df[f'{col}_y'], inplace=True)
            df[f'{col}_y'].fillna(df[f'{col}_x'], inplace=True)
    
    for col in ['Form template', 'Form template version', 'Request Type', 'Risk Level', 'Audit Opinion']:
        df[f'{col}_x'].ffill(inplace=True)
        df[f'{col}_y'].ffill(inplace=True)
    
    bad_cols = ['Request Type', 'Risk Level', 'Audit Opinion']
    for col in bad_cols:
        df.loc[(df['Page name_x'] == 'Title') & (df[f'{col}_x'].isin(["", "-", np.nan])), f'{col}_x'] = 'Not Entered'
        df[f'{col}_x'].ffill(inplace=True)
    
    for col in ['Form template', 'Form template version', 'Request Type', 'Risk Level', 'Audit Opinion']:
        df[col] = df[f'{col}_x']
    
    return df

def add_data_from_masterfile(all_df, master_df):
    master_cols = ['Audit Opinion', 'Risk Level']
    for col in master_cols:
        temp_df = master_df[['Form_instance_ID', col]].drop_duplicates()
        all_df = pd.merge(all_df, temp_df, on='Form_instance_ID', how='left', suffixes=('', '_master'))
        all_df.loc[(all_df[col] == "Not Entered") & (all_df[col+'_master'].notna()), col] = all_df[col+'_master']
        all_df.drop(columns=[col+'_master'], inplace=True)
    
    all_df['Assignee'] = all_df['Assignee'].str.replace('--', '-')
    all_df['Role'] = all_df['Assignee'].str.split('-', expand=True)[1]
    all_df['Assignee'] = all_df['Assignee'].str.split('-', expand=True)[0]
    all_df['Page name'] = all_df['Page name'].str.strip()
    all_df['Status'] = all_df['Status'].str.strip()
    
    all_df['SLA_Date'] = all_df['Completed'].fillna(date.today())
    
    time_cols = ['Created', 'Started', 'Last Updated', 'Completed', 'SLA_Date']
    for col in time_cols:
        all_df[col] = pd.to_datetime(all_df[col], errors='coerce', infer_datetime_format=True)
    all_df['month_year'] = all_df['Created'].dt.to_period('M')
    for col in time_cols:
        all_df[col] = all_df[col].dt.date
    
    return all_df

def run_script_b(cleaned_df):
    st.title("Valid8ME Data Merge")

    st.write("Upload Master Data:")
    file1 = st.file_uploader("Upload Master Data", type=['xlsx'], key="file1")

    if st.button("Merge Data Process"):
        if file1 is not None:
            try:
                df1 = pd.read_excel(file1, engine='openpyxl')
                df2 = cleaned_df

                df1.columns = df1.columns.str.strip()
                df2.columns = df2.columns.str.strip()

                st.write("Columns in the master dataframe:")
                st.write(df1.columns.tolist())
                st.write("Columns in the cleaned dataframe:")
                st.write(df2.columns.tolist())

                df1['Form_instance_ID'] = df1['Form_instance_ID'].astype(str)
                df2['Form_instance_ID'] = df2['Form_instance_ID'].astype(str)

                required_columns = ['Form_instance_ID', 'Page name']
                for col in required_columns:
                    if col not in df1.columns:
                        st.warning(f"Column '{col}' is missing in the master dataframe.")
                        return
                    if col not in df2.columns:
                        st.warning(f"Column '{col}' is missing in the cleaned dataframe.")
                        return

                merged_df = pd.merge(df1, df2, on=['Form_instance_ID', 'Page name'], how='outer')

                st.write("Columns after merge:")
                st.write(merged_df.columns.tolist())

                merged_df = fill_missing_values(merged_df)

                st.write("Columns after fill_missing_values:")
                st.write(merged_df.columns.tolist())

                merged_df = add_data_from_masterfile(merged_df, df1)

                st.write("Columns after add_data_from_masterfile:")
                st.write(merged_df.columns.tolist())

                merged_file_path = "merged_file.xlsx"
                merged_df.to_excel(merged_file_path, index=False)

                csv_data = merged_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Download CSV", data=csv_data, file_name="Valid8MeAggregate.csv", mime="text/csv")

                st.success("Merged Excel file saved successfully.")
            except Exception as e:
                st.warning(f"Merge failed: {e}")
        else:
            st.warning("Please upload the Master Data file.")

# Main integration
def main():
    st.sidebar.title("Process Selector")
    process = st.sidebar.selectbox("Select Process", ["Clean Data", "Merge Data"])

    if process == "Clean Data":
        cleaned_df = run_script_a()
        if cleaned_df is not None:
            st.write("Data cleaned and saved successfully. Proceed to the 'Merge Data' process.")
    elif process == "Merge Data":
        cleaned_df = None
        file_path = st.sidebar.text_input("Enter path to cleaned data (Valid8MeOutput-clean.xlsx):")
        if file_path:
            try:
                cleaned_df = pd.read_excel(file_path, engine='openpyxl')
            except Exception as e:
                st.warning(f"Failed to load cleaned data: {e}")
        if cleaned_df is not None:
            run_script_b(cleaned_df)

if __name__ == "__main__":
    main()
