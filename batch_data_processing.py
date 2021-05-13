import pandas as pd
import surface_coverage_processing as s
import fluorescence_processing as f
import volumetric_processing as v
import numpy as np
import os
import bioformats
import javabridge
import batch_analysis_functions as b

# read in data from spreadsheet
master_info_df=pd.read_excel('Flow Assay Log.xlsx',sheet_name='Kinetic Data')
dynamic_master=pd.DataFrame()
metric_master=pd.DataFrame()
old_dynamic_master=pd.read_csv('time_series_data.csv')
old_metric_master=pd.read_csv('metrics_data.csv')

# -------info to copy from into df to results of analysis
info=['Date','Donor','Donor No','dP (kPa)','Blood Conditions',
      'Surface','Channel Number','Assay ID','Device']

current_path=os.getcwd()
javabridge.start_vm(class_path=bioformats.JARS)
# A for loop to loop through the cells in the excel sheet where I store all of the relevant information for the assays
for index, row in master_info_df.iterrows():
    kinetic_path = row['File Path']
    print('---------Row: ', str(index+2),' ',kinetic_path)
    # Only do analysis for cells where I specify a file location since some cells don't have this
    if not pd.isna(kinetic_path):
        # since a relative path is passed in from the excel sheet we need to add the absolute path 
        # to that 
        # from Cell Sense they dump the channels of all photos into the same folder but distinguish them by file type
        path= kinetic_path
        # We have an option in the excel sheet to pull the data from the old master csvs for a given assay if we don't need to analyze it
        if row['Analyze Assay']=='N':
           print('\t','Read in From Previous Analysis')
           dynamic_df=old_dynamic_master[old_dynamic_master['Assay ID']==row['Assay ID']]
           met_df=old_metric_master[old_metric_master['Assay ID']==row['Assay ID']]
        else:
            # Generate a dictionary that allows us to specify the options we want to pass into our function to evaluate mean fluorescence and metrics
            s_options = dict(
                             stats=True,  # argument telling function to return summary statistics
                             show_linear=True, # argument telling the function to show show the summary stats plotted over the raw data so we can verify they are
                             # being evaluated properly
                             vsi=True, # analyze vsi file and not tiffs
                             show=True, # show the analyzed images
                             bw_eval=False, 
                             edge=True, # evaluating using the edgefinder and not through conventional
                                         # thresholding 
                             auto_thresh=True,
                             filter_type='otsu',
                             t_lag_level=0.03,
                             cycle_vm=False,
                             meta_number=int(row['Meta Number']),
                             zero_index=int(row['Zero Index']),
                             image_channel=1,
                             meta_stage_loop=True,
                             t_sample=10
                             )
            # Optional things that are specified for the functions
            if not pd.isna(row['Zero Index']):
                s_options['zero_index']=row['Zero Index']
            # if a background is specified we feed that into the fluorescence processing 
            if not pd.isna(row['Background']):
                s_options['background']=row['Background']
            if row['Stage Loop']=='N':
                s_options['meta_stage_loop']=False
            sc, sc_m = s.surface_coverage_time_series(path,**s_options) 
            f_opt=s_options
            f_opt['t_lag_level']=10
            remove=['show','bw_eval','filter_type','edge','auto_thresh']
            for r in remove:
                f_opt.pop(r)
            fl,fl_m=f.fluorescence_time_series(path,**s_options)
            fl=fl.drop(columns=['Time (s)'])
            sc=sc.drop(columns=['Time (s)'])
            vol_opts=f_opt
            vol_opts['t_lag_level']=10
            vol_opts.pop('vsi')
            vol,vol_m=v.single_volume_time_series(path,**vol_opts)
            dynamic_df=pd.concat([vol,fl,sc],axis=1)
            dynamic_df['Thrombus Height (um)']=dynamic_df['Thrombus Volume (um^3)']/dynamic_df['Surface Area (um^2)']
            # dynamic_df=fl
            met_df=pd.concat([sc_m,fl_m,vol_m],axis=1)
            met_df['H Max (um)']=met_df['V Max']/met_df['SA Max']
            # met_df=fl_m
            # store info about assay conditions into analsysi
            b.store_info(dynamic_df,row,info)
            b.store_info(met_df,row,info)
        # Store all of this data in dataframes so we can easily plot all of it together
        dynamic_master=dynamic_master.append(dynamic_df,ignore_index=True)
        metric_master=metric_master.append(met_df,ignore_index=True)
        dynamic_master.to_csv('time_series_data.csv',index=False)
        metric_master.to_csv('metrics_data.csv',index=False)
        # metric_platelet_df=metric_platelet_df.append(m,ignore_index=True)        
javabridge.kill_vm()
# ----------------Normalize data to max of that day
# Function to do normalization with

# Variables I want to normalize by
# normalization_variables=['Donor No']
# for i in range(len(normalization_variables)):
#     # Perform normalization on all of the storage dfs
#     dynamic_df=normalize_by(normalization_variables[i],'Surface Coverage',dynamic_df,master_info_df)
#     metric_platelet_df=b.normalize_by(normalization_variables[i],'Max',metric_platelet_df,master_info_df)
#     metric_platelet_df=b.normalize_by(normalization_variables[i],'Slope',metric_platelet_df,master_info_df)



# metric_platelet_df.to_csv('metrics_data.csv',index=False)