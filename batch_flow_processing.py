import fluorescence_processing as f
import pandas as pd
import flow_rate_analysis as fl
import numpy as np
import batch_analysis_functions as b

def store_info(df1,df2,info):
    # df1 = df you are copying info to
    # df2 = df you are copying from
    # info = list of strings that you are storing
    for i in range(len(info)):
        df1[info[i]]=np.array([df2[info[i]]]*len(df1))

# read in experimental conditions
df=pd.read_excel('Flow Assay Log.xlsx')
# choose what metadata I want to store with the analyzed results
info=['Date','Donor','Donor No','Channel Number', 'Assay ID','dP (kPa)',
      'Surface']
flow_curves=pd.DataFrame()
flow_metrics=pd.DataFrame()
# Iterate through spreadsheet
for index,row in df.iterrows():
    # print metadata about assay
    # analyze flowrate data
    flow_path = row['Flow Path']
    channel=row['Channel Number']
    read_csv=row['Read CSV']
    if not pd.isna(flow_path):

        f_options=dict(channel=channel,get_metrics=True)
        if read_csv=='Y':
            loop_curve=pd.read_csv(flow_path)
            loop_met=fl.compute_metrics(loop_curve)
            
        else:
            loop_curve,loop_met=fl.flowrates_TMDS(flow_path,**f_options)
        # store metadata with flowrate data
        b.store_info(loop_curve,row,info)
        b.store_info(loop_met,row,info)
        flow_curves=flow_curves.append(loop_curve,ignore_index=True)
        flow_metrics=flow_metrics.append(loop_met,ignore_index=True)
    else:
        loop_met=pd.DataFrame({'Absolute Clot Time (min)':'nan',
                                 'Absolute Clot Time (s)':'nan',
                                 'Endpoint Flowrate (uL/min)':'nan',
                                 'Relative Clot Time (min)':'nan',
                                 'Relative Clot Time (s)':'nan'
                                 },index=[0])
        flow_metrics = flow_metrics.append(loop_met, ignore_index=True)
# write analyzed data to csvs
flow_metrics.to_csv('flow_metrics.csv',index=False)
flow_curves.to_csv('flow_curves.csv',index=False)


