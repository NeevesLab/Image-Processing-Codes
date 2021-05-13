import pandas as pd
import fluorescence_processing as f
import numpy as np
import os
import batch_analysis_functions as b
import javabridge
import bioformats
# read in data from spreadsheet
master_info_df=pd.read_excel('Flow Assay Log.xlsx',sheet_name='Kinetic Data')
# Make 2 datafames to store our analysis result in
dynamic_platelet_df=pd.DataFrame()
metric_platelet_df=pd.DataFrame()
# <<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# extra experiment metadata you want to print and save in the assay 
info=['Date','Donor','Donor No','Shear Rate (s^-1)','Surface','Channel Number','Assay ID',
      'Platelet Count (x10^3 cells/uL)','Hematocrit']
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

current_path=os.getcwd()
# start vm
javabridge.start_vm(class_path=bioformats.JARS)
# A for loop to loop through the cells in the excel sheet where I store all of the relevant information for the assays
for index, row in master_info_df.iterrows():
    b.print_info(row,info)
    kinetic_path = row['File Path']
    
    # Only do analysis for cells where I specify a file location since some cells don't have this
    if not pd.isna(kinetic_path):
        # since a relative path is passed in from the excel sheet we need to add the absolute path 
        # to that 
        abs_path=os.getcwd()+kinetic_path
        abs_path=abs_path.replace('\\','/')
        # Generate a dictionary that allows us to specify the options we want to pass into our function to evaluate mean fluorescence and metrics
        f_options = dict(stats=True,  # argument telling function to return summary statistics
                         # argument telling the function to show show the summary stats plotted over the raw data so we can verify they are
                         # being evaluated properly
                         show_linear=True,
                         t_lag_thresh=150,
                         vsi=True,
                         cycle_vm=False
                         )
        #<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        #------------ Important Modifiable Data --------
        options_spreadsheet=['Zero Index','Background','Picture Interval (s)']
        options_function_names=['zero_index','background','interval']
        # <<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        f_options=b.search_for_options(options_spreadsheet,options_function_names,
                                       row,f_options)
        # <<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><>>>>>>>>>>>>>>
        
        fl, m = f.fluorescence_time_series(abs_path,**f_options) 
        # store info about assay conditions into analsysi
        b.store_info(m,row,info)
        b.store(fl,row,info)
#         print_info(row,info)
        # Store all of this data in dataframes so we can easily plot all of it together
        dynamic_platelet_df=dynamic_platelet_df.append(fl,ignore_index=True)
        metric_platelet_df=metric_platelet_df.append(m,ignore_index=True)          

javabridge.kill_vm()
# Save data to .csvs
dynamic_platelet_df.to_csv('time_series_data.csv',index=False)
metric_platelet_df.to_csv('metrics_data.csv',index=False)