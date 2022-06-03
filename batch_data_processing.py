import pandas as pd
import fluorescence_processing as f
import os
import bioformats
import javabridge
import batch_analysis_functions as b

# read in data from spreadsheet
sheet_path="Experiment Log.xlsx"
sheet_path=sheet_path.replace('\\','/')
master_info_df=pd.read_excel(sheet_path)
# declare dataframes that will store our final results
dynamic_master=pd.DataFrame()
metric_master=pd.DataFrame()
# define set of default options for data processing
default_options=dict(stats=True, # argument telling function to return summary statistics
                 show_linear=True, # argument telling the function to show show the summary stats plotted over the raw data so we can verify they are
                 # being evaluated properly
                 t_lag_level=0.01, # threshold to set for lag time level
                 cycle_vm=False, # telling javabridge to stay on because function will turn it off by default
                 image_channel=0, # selecting image channel to analyze, this corresponds to imaging mode (FITC,TRITC,BF,etc)
                 meta_number=1, # default number in file name of oex file to read in
                 t_cutoff=5*60, # Time we want to analyze assay to in seconds
                 zero_index=1 # image number we want to call t=0
                 )
# Determining which info is metadata to be passed into the results and which is 
# essential data processing options to pass into data processing
stored_metadata=[]
options_to_search=[]
for c in master_info_df.columns:
    if  c in default_options.keys():
        options_to_search.append(c)
    else: 
        stored_metadata.append(c)
# Begin data processing using for loops 
current_path=os.getcwd()
javabridge.start_vm(class_path=bioformats.JARS)
# A for loop to loop through the cells in the excel sheet where I store all of the relevant information for the assays
for index, row in master_info_df.iterrows():
    # read in filepath
    path = row['Experiment Filepath']
    print('---------Row: ', str(index+2),' ',path)
    # Only do analysis for cells where I specify a file location since some cells don't have this
    if not pd.isna(path):
        # since a relative path is passed in from the excel sheet we need to add the absolute path 
        # to that 
        # from Cell Sense they dump the channels of all photos into the same folder but distinguish them by file type
        path=path.replace('\\','/')
        path=path+'.vsi'
        # We have an option in the excel sheet to pull the data from the old master csvs for a given assay if we don't need to analyze it
        if row['Analyze']=='N':
           print('\t','Read in From Previous Analysis')
           old_dynamic_master=pd.read_csv('time_series_data.csv')
           old_metric_master=pd.read_csv('metrics_data.csv')
           dynamic_df=old_dynamic_master[old_dynamic_master['Assay ID']==row['Assay ID']]
           met_df=old_metric_master[old_metric_master['Assay ID']==row['Assay ID']]
        else:
            # Generate a dictionary that allows us to specify the options we want to pass into our function to evaluate mean fluorescence and metrics
            options = default_options
            # Pulling options that are specifically passed into excel sheet 
            # into the data processing options 
            for entry in options_to_search:
                if not pd.isna(row[entry]):
                    options[entry]=row[entry]
            # compute the mean FI vs time data 
            dio_kin,dio_met=f.fluorescence_time_series(path,**options)
            # met_df=fl_m
            # store info about assay conditions into analsysi
            b.store_info(dio_kin,row,stored_metadata)
            b.store_info(dio_met,row,stored_metadata)
        # Store all of this data in dataframes so we can easily plot all of it together
        dynamic_master=pd.concat([dynamic_master,dio_kin],axis=0)
        metric_master=pd.concat([metric_master,dio_met],axis=0)
    # finally store results as a csv for downstream analysis 
    dynamic_master.to_csv('time_series_data.csv',index=False)
    metric_master.to_csv('metrics_data.csv',index=False)
# finally turn off javabrdge
javabridge.kill_vm()
