# import streamlit as st
# import pandas as pd
# import re
# import io

# st.set_page_config(page_title="Ramp Invoice Processor", layout="wide")
# st.title("📄 Ramp Invoice Processor (input.xlsx + compare.xlsx)")

# # === Upload files
# input_file = st.file_uploader("Upload Input Excel", type=['xlsx'], key="input")
# compare_file = st.file_uploader("Upload Compare Excel (Sheet2)", type=['xlsx'], key="compare")

# if input_file and compare_file:
#     if st.button("🔁 Process and Generate Files"):
#         # === Read files
#         input_df = pd.read_excel(input_file)
#         compare_df = pd.read_excel(compare_file, sheet_name='Sheet2')

#         # === Normalize and map (same logic as script)
#         vendor_aliases = {
#             "granite telecommunications": "granite communications",
#             "windstream": "windstream communication",
#             "charter communications": "spectrum business",
#         }

#         def normalize_name(name):
#             name = str(name).strip().lower()
#             name = re.sub(r'\s+\d+$', '', name)
#             name = re.sub(r'\(.*?\)', '', name)
#             return name.strip()

#         def custom_normalize(name):
#             name_clean = normalize_name(name)
#             if "charter" in name_clean:
#                 return "spectrum business"
#             return vendor_aliases.get(name_clean, name_clean)

#         compare_df['Full Address Key'] = compare_df['Address'].astype(str).str.strip().str.lower()
#         compare_df['Clean Vendor Name'] = compare_df['Vendor Name'].apply(custom_normalize)
#         compare_df['Display Vendor Name'] = compare_df.iloc[:, 0]
#         vendor_name_mapping = compare_df.set_index(
#             ['Clean Vendor Name', 'Full Address Key']
#         )['Display Vendor Name'].to_dict()

#         input_df['Full Address Key'] = (
#             input_df['Vendor Address 1'].fillna('').astype(str).str.strip().str.lower() + ' ' +
#             input_df['Vendor Address 2'].fillna('').astype(str).str.strip().str.lower()
#         ).str.strip()
#         input_df['Clean Vendor Name'] = input_df['Vendor Name 1'].apply(custom_normalize)

#         input_df['Vendor Name Final'] = input_df.apply(
#             lambda row: vendor_name_mapping.get(
#                 (row['Clean Vendor Name'], row['Full Address Key']),
#                 row['Vendor Name 1']
#             ), axis=1)

#         input_df['Invoice Date'] = pd.to_datetime(input_df['Invoice Date'], errors='coerce').dt.strftime('%Y-%m-%d')
#         input_df['Due Date'] = pd.to_datetime(input_df['Due Date'], errors='coerce').dt.strftime('%Y-%m-%d')

#         final_output = input_df[[
#             'Vendor Name Final', 'Customer Vendor Account Number', 'Invoice Number',
#             'Invoice Date', 'Due Date', 'Net Amount', 'Cust Id'
#         ]]
#         final_output.columns = [
#             'Vendor name', 'Description (optional)', 'Invoice number',
#             'Invoice date', 'Due date', 'Line item amount', 'Line item description'
#         ]
#         final_output['Description (optional)'] = final_output['Description (optional)'].apply(
#             lambda x: f'="{x}"' if pd.notnull(x) and x != '' else '')
#         final_output['Accounting date (optional)'] = ''
#         final_output['Currency'] = 'USD'
#         final_output['Vendor memo (optional)'] = ''
#         final_output['Payment method (optional)'] = ''
#         final_output = final_output[[
#             'Vendor name', 'Description (optional)', 'Invoice number', 'Invoice date',
#             'Accounting date (optional)', 'Due date', 'Currency',
#             'Line item amount', 'Line item description',
#             'Vendor memo (optional)', 'Payment method (optional)'
#         ]]

#         # === Save s1.csv to memory
#         s1_csv = io.StringIO()
#         final_output.to_csv(s1_csv, index=False)
#         s1_csv.seek(0)

#         # === Grouping logic
#         df = pd.read_csv(s1_csv)
#         df['Line item amount'] = pd.to_numeric(df['Line item amount'], errors='coerce').fillna(0)

#         def strip_excel_quotes(series):
#             return series.astype(str).str.replace('="', '', regex=False).str.replace('"', '', regex=False)

#         for col in ['Description (optional)', 'Invoice number', 'Invoice date', 'Due date']:
#             df[col] = strip_excel_quotes(df[col])

#         def group_concat(series):
#             return ', '.join(series.dropna().astype(str).unique())

#         def get_latest_date(series):
#             dates = pd.to_datetime(series.dropna().astype(str), errors='coerce')
#             latest = dates.max()
#             return latest.strftime('%Y-%m-%d') if pd.notnull(latest) else ''

#         grouped_df = df.groupby("Vendor name", as_index=False).agg({
#             'Description (optional)': lambda x: f'="{" ,".join(x.astype(str).dropna().unique())}"',
#             'Invoice number': lambda x: ', '.join(x.astype(str).dropna().unique()),
#             'Invoice date': get_latest_date,
#             'Accounting date (optional)': group_concat,
#             'Due date': get_latest_date,
#             'Currency': group_concat,
#             'Line item amount': lambda x: round(x.sum(), 2),
#             'Line item description': group_concat,
#             'Vendor memo (optional)': group_concat,
#             'Payment method (optional)': group_concat
#         })

#         # === Save s1_grouping.csv to memory
#         s1_group_csv = io.StringIO()
#         grouped_df.to_csv(s1_group_csv, index=False)
#         s1_group_csv.seek(0)

#         st.success("✅ Both files generated successfully!")

#         st.download_button("⬇️ Download s1.csv", data=s1_csv.getvalue(), file_name="s1.csv", mime="text/csv")
#         st.download_button("⬇️ Download s1_grouping.csv", data=s1_group_csv.getvalue(), file_name="s1_grouping.csv", mime="text/csv")


import streamlit as st
import pandas as pd
import re
import io

# === Page Config
st.set_page_config(page_title="Ramp Invoice Processor", layout="wide")
st.title("📄 Ramp Invoice Processor")

# === Load compare.xlsx from disk
@st.cache_data
def load_compare_file():
    return pd.read_excel("compare.xlsx", sheet_name="Sheet2")

compare_df = load_compare_file()

# === Vendor alias mapping
vendor_aliases = {
    "granite telecommunications": "granite communications",
    "windstream": "windstream communication",
    "charter communications": "spectrum business",
}

def normalize_name(name):
    name = str(name).strip().lower()
    name = re.sub(r'\s+\d+$', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

def custom_normalize(name):
    name_clean = normalize_name(name)
    if "charter" in name_clean:
        return "spectrum business"
    return vendor_aliases.get(name_clean, name_clean)

# === Upload input file
input_file = st.file_uploader("Upload Input Excel file (input.xlsx)", type=["xlsx"])

# === Process
if input_file:
    if st.button("🔁 Process and Generate Files"):
        input_df = pd.read_excel(input_file)

        # Normalize compare file
        compare_df['Full Address Key'] = compare_df['Address'].astype(str).str.strip().str.lower()
        compare_df['Clean Vendor Name'] = compare_df['Vendor Name'].apply(custom_normalize)
        compare_df['Display Vendor Name'] = compare_df.iloc[:, 0]

        vendor_name_mapping = compare_df.set_index(
            ['Clean Vendor Name', 'Full Address Key']
        )['Display Vendor Name'].to_dict()

        # Normalize input
        input_df['Full Address Key'] = (
            input_df['Vendor Address 1'].fillna('').astype(str).str.strip().str.lower() + ' ' +
            input_df['Vendor Address 2'].fillna('').astype(str).str.strip().str.lower()
        ).str.strip()
        input_df['Clean Vendor Name'] = input_df['Vendor Name 1'].apply(custom_normalize)

        input_df['Vendor Name Final'] = input_df.apply(
            lambda row: vendor_name_mapping.get(
                (row['Clean Vendor Name'], row['Full Address Key']),
                row['Vendor Name 1']
            ), axis=1)

        input_df['Invoice Date'] = pd.to_datetime(input_df['Invoice Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        input_df['Due Date'] = pd.to_datetime(input_df['Due Date'], errors='coerce').dt.strftime('%Y-%m-%d')

        final_output = input_df[[
            'Vendor Name Final', 'Customer Vendor Account Number', 'Invoice Number',
            'Invoice Date', 'Due Date', 'Net Amount', 'Cust Id'
        ]]
        final_output.columns = [
            'Vendor name', 'Description (optional)', 'Invoice number',
            'Invoice date', 'Due date', 'Line item amount', 'Line item description'
        ]

        final_output['Description (optional)'] = final_output['Description (optional)'].apply(
            lambda x: f'="{x}"' if pd.notnull(x) and x != '' else '')

        final_output['Accounting date (optional)'] = ''
        final_output['Currency'] = 'USD'
        final_output['Vendor memo (optional)'] = ''
        final_output['Payment method (optional)'] = ''

        final_output = final_output[[
            'Vendor name', 'Description (optional)', 'Invoice number', 'Invoice date',
            'Accounting date (optional)', 'Due date', 'Currency',
            'Line item amount', 'Line item description',
            'Vendor memo (optional)', 'Payment method (optional)'
        ]]

        # === Save s1.csv to memory and session
        s1_csv = io.StringIO()
        final_output.to_csv(s1_csv, index=False)
        st.session_state['s1_csv'] = s1_csv.getvalue()

        # === Grouping logic
        df = pd.read_csv(io.StringIO(st.session_state['s1_csv']))
        df['Line item amount'] = pd.to_numeric(df['Line item amount'], errors='coerce').fillna(0)

        def strip_excel_quotes(series):
            return series.astype(str).str.replace('="', '', regex=False).str.replace('"', '', regex=False)

        for col in ['Description (optional)', 'Invoice number', 'Invoice date', 'Due date']:
            df[col] = strip_excel_quotes(df[col])

        def group_concat(series):
            return ', '.join(series.dropna().astype(str).unique())

        def get_latest_date(series):
            dates = pd.to_datetime(series.dropna().astype(str), errors='coerce')
            latest = dates.max()
            return latest.strftime('%Y-%m-%d') if pd.notnull(latest) else ''

        grouped_df = df.groupby("Vendor name", as_index=False).agg({
            'Description (optional)': lambda x: f'="{" ,".join(x.astype(str).dropna().unique())}"',
            'Invoice number': lambda x: ', '.join(x.astype(str).dropna().unique()),
            'Invoice date': get_latest_date,
            'Accounting date (optional)': group_concat,
            'Due date': get_latest_date,
            'Currency': group_concat,
            'Line item amount': lambda x: round(x.sum(), 2),
            'Line item description': group_concat,
            'Vendor memo (optional)': group_concat,
            'Payment method (optional)': group_concat
        })

        s1_group_csv = io.StringIO()
        grouped_df.to_csv(s1_group_csv, index=False)
        st.session_state['s1_group_csv'] = s1_group_csv.getvalue()

        st.success("✅ Files processed and ready for download.")

# === Always show download buttons if available
if 's1_csv' in st.session_state and 's1_group_csv' in st.session_state:
    st.download_button(
        "⬇️ Download s1.csv",
        data=st.session_state['s1_csv'],
        file_name="s1.csv",
        mime="text/csv",
        key="download_s1"
    )
    st.download_button(
        "⬇️ Download s1_grouping.csv",
        data=st.session_state['s1_group_csv'],
        file_name="s1_grouping.csv",
        mime="text/csv",
        key="download_group"
    )
