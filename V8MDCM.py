import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date
import numpy as np

# Data Clean (Script A) components
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

# Data Merge (Script B) components
def fill_missing_values(df):
    # Example implementation for filling missing values
    df.fillna(method='ffill', inplace=True)
    return df

def add_data_from_masterfile(all_df, master_df):
    # Example implementation for adding data from master file
    return pd.merge(all_df, master_df, on='Form_instance_ID', how='left')

def run_script_b():
    st.title("Valid8ME Data Merge")

    st.write("Upload Master Data:")
    file1 = st.file_uploader("Upload Master Data", type=['xlsx'], key="file1")

    st.write("Upload Cleaned Data:")
    cleaned_file = st.file_uploader("Upload Cleaned Valid8Me Output", type=['xlsx'], key="cleaned_file")

    if st.button("Merge Data Process"):
        if file1 is not None and cleaned_file is not None:
            try:
                df1 = pd.read_excel(file1, engine='openpyxl')
                df2 = pd.read_excel(cleaned_file, engine='openpyxl')

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

                # Other operations...
                st.write("Columns after additional processing:")
                st.write(merged_df.columns.tolist())

                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    merged_df.to_excel(writer, index=False, sheet_name='Sheet1')
                output.seek(0)

                st.download_button(label="Download Merged Excel", data=output, file_name="Valid8MeAggregate.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.success("Merged Excel file saved successfully.")
            except Exception as e:
                st.warning(f"Merge failed: {e}")
        else:
            st.warning("Please upload both the Master Data and Cleaned Valid8Me Output files.")

# Main integration
def main():
    st.sidebar.title("Process Selector")
    process = st.sidebar.selectbox("Select Process", ["Clean Data", "Merge Data"])

    if process == "Clean Data":
        run_script_a()
    elif process == "Merge Data":
        run_script_b()

if __name__ == "__main__":
    main()
