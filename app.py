import pandas as pd
import streamlit as st

#create page configurations to provide a Meta Title and main header
st.set_page_config(page_title="Cannibalisation Data Review", initial_sidebar_state="auto")
st.title('Cannibalisation Tool')

# read the csv file and create the dataframe
# update df = pd.read_csv('your_file.csv') to:
uploaded_file = st.file_uploader("Use a GSC API export that includes query and page as the dimensions, exporting clicks, impressions, avg. position and CTR", type='csv')

#update to include slider so you can customise your cannibalisation threshold
impression_th = st.slider("Input what impression share threshold is required to be marked as potential cannibalisation", min_value=0.0, max_value=1.0, value=0.1) 
click_th = st.slider("Input what click share threshold is required to be marked as potential cannibalisation", min_value=0.0, max_value=1.0, value=0.1)

#update to add "uploaded_file"
if uploaded_file is not None:

    @st.cache
    def create_df(file):

        df = pd.read_csv(uploaded_file)
        # group the data by the query column and calculate the total impressions and total clicks for each query
        df_impressions = df.groupby('query')['impressions'].transform('sum')
        df_clicks = df.groupby('query')['clicks'].transform('sum')

        # create new columns in the original dataframe with the total impressions and total clicks for each query
        df['total_impressions'] = df_impressions
        df['total_clicks'] = df_clicks

        # create a new column that calculates the impressions share for each page for each query
        df['impressions_share'] = df['impressions'] / df['total_impressions'].fillna(0)

        # create a new column that calculates the clicks share for each page for each query
        df['clicks_share'] = df['clicks'] / df['total_clicks'].fillna(0)

        #had to rerun this again to get the right approach
        df['more_than_one_page_over_impr_cann_threshold'] = df.groupby('query')['impressions_share'].transform(lambda x: (x >= impression_th).sum() > 1)

        # create a new column that shows if there are more than one pages with 10% or more clicks share
        df['more_than_one_page_over_clicks_cann_threshold'] = df.groupby('query')['clicks_share'].transform(lambda x: (x >= click_th).sum() > 1)

        filtered_df = df[(df['more_than_one_page_over_impr_cann_threshold'] == True) | (df['more_than_one_page_over_clicks_cann_threshold'] == True)]
        return filtered_df
    
    df = create_df(uploaded_file)
    #create your filters

    st.write("If you'd rather just export the data in full and use another tool to find what you need, you can export the full data table below, otherwise scroll further to filter your dataset.")
    csv_1 = df.to_csv(index=False)
    st.download_button('Download Full Data as CSV', csv_1, file_name = 'Full data - unfiltered.csv', mime='text/csv')

    st.header("Output table")
    st.write("The table below is filtered to only queries with 2 or more pages with over 10% of either clicks or impressions. Now we have the output, we can start adding filters so we get exactly what we want")

    col1,col2 = st.columns(2)

    with col1:
        filter_tot_imp = st.select_slider('Filter by total query impressions', options=[0,1,10,50,100,200,300,400,500,1000,10000], value=0)
    with col2:
        filter_tot_cli = st.select_slider('Filter by total query clicks', options=[0,1,10,50,100,200,300,400,500,1000,10000], value=0)
    
    col3,col4 = st.columns(2)

    with col3:
        filter_imp_share = st.slider('Find out the biggest problems by filtering by impression share', min_value=0.0, max_value=1.0, value=0.0)
    with col4:
        filter_imp_click = st.slider('Find out the biggest problems by filtering by click share', min_value=0.0, max_value=1.0, value=0.0)

    # print the new dataframe

    filtered_df = df[(df['total_impressions'] >= filter_tot_imp) & (df['total_clicks'] >= filter_tot_cli) & (df['impressions_share'] >= filter_imp_share) & (df['clicks_share'] >= filter_imp_click)]
    st.write("There are ", len(filtered_df.index), " rows in this current filtered dataframe and ", filtered_df['query'].unique().size, " unique queries.")
    st.dataframe(filtered_df)
    csv = filtered_df.to_csv(index = False)
    st.download_button('Download Table as CSV', csv, file_name = 'output.csv', mime='text/csv')
