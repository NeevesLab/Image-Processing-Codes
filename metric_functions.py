import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# function that does pre processing to the data, fits the metrics, shows graphs, 
# and compiles the metrics
def get_metrics(df,show_linear=False,max_t_lag=5*60,t_lag_level=200,interval=1):
    # get min and max surface coverages
    max_val = np.max(df['Zero Mean'])
    # resample series to finer grain for better analysis 
    x,y=interpolate_series(df)
    # get index of 80% val of max
    max_index=get_max_index(x,y)
    # get lag time and update certain indices if need be
    t_lag,t_lag_index,max_index=get_lag_time(x,y,t_lag_level,max_t_lag,max_index,max_val)
    # Get slope of linear region
    slope,intercept=get_slope(x,y,t_lag_index,max_index)
    if show_linear:
        plt.figure(1)
        y_linear = x[t_lag_index:max_index] * slope + intercept
        plt.plot(x[t_lag_index:max_index], y_linear, '-r', label='Linear Fit', linewidth=2)
        # Plot raw data 
        plt.plot(df['time (s)'], df['Zero Mean'], 'ob', label='Experimental Data',alpha=0.5)
        # plot lag time as vertical line
        plt.axvline(x=t_lag, color='k', linestyle='--', label='T-lag')
        # plot max  as fluorescencehorizontal line 
        plt.axhline(y=max_val, color='g', linestyle='--', label='Max')
        plt.xlabel('time (s)')
        plt.ylabel('Fluorescence Intensity')
        plt.title('Experimental Data and Fitted Kinetic Metrics')
        plt.legend()
        plt.show()
    # Store data using pandas 
    metrics = pd.DataFrame([{'F T-lag': t_lag, 'F Max': max_val, 'F Slope': slope}])
    return metrics

def get_slope(x,y,t_lag_index,max_index,metric='max_slope',min_fit=0.5):
    min_fit_length = int(round(min_fit*(len(x)+1)))
    if max_index>=100:
        iterator=int(round(len(x)/100))
    else:
        iterator=1
    # Now the code chooses the slope on the criteria of either:
    # - getting the largest possible slope of a line that is min_fit*the fitting length
    if metric=='max_slope':
        coefs,slope_index=max_slope(x,y,t_lag_index,max_index,iterator,min_fit_length)
    # - or by getting the most linear region for the fitting space
    if metric=='best_fit':
        # Search on the interval from t-lag to 2% from the max value
        coefs=chi_squared_min(x,y,t_lag_index,max_index,iterator,min_fit_length)
    slope=coefs[0]
    # no negative slopes!
    if slope<0: slope =0
    try:
        coefs[1]
    except:
        intercept=0
    else:
        intercept=coefs[1]
    return slope,intercept

def max_slope(x,y,t_lag_index,max_index,iterator,min_fit_length=25):
    grad=np.gradient(y,x)
    slope=np.max(grad)
    slope_index=np.where(grad==slope)[0]
    intercept=y[t_lag_index]
    coefs=np.array([slope,intercept])
    return coefs,slope_index

def chi_squared_min(x,y,t_lag_index,max_index,iterator,min_fit_length):
    chi_min=1E-3
    for i in range(t_lag_index, max_index ,iterator):
        for j in range(i+min_fit_length, max_index,iterator):
            # If the array is zero 
            if not x[i:j].size or not y[i:j].size:
                print ('Array Empty in Loop')
                print (i,j)
            elif not np.absolute(j-i)<min_fit_length:
                coefs_loop = np.polyfit(x[i:j], y[i:j], 1)
                y_linear = x * coefs_loop[0] + coefs_loop[1]
                chi = 0
                for k in range(i, j):
                    chi += (y_linear[k] - y[k]) ** 2

                if chi < chi_min:
                    i_best = i
                    j_best = j
                    chi_min = chi
                # print 'Chi-min: '+str(chi_min)
                # print 'Chi:'+str(chi)
    if not x[i_best:j_best].size or not y[i_best:j_best].size:
        print('Array Empty Outside of Loop')
        print(i_best,j_best)
        coefs=[float('nan')]
    else:
        coefs = np.polyfit(x[i_best:j_best], y[i_best:j_best], 1)
    return coefs

# Get index for first data point 2% away from the max
def get_lag_time(x,y,t_lag_level,max_t_lag,max_index,maxSC):
    y=y-y[0]
    t_lag_index=None
    for i in range(len(y)):
        # If the surface coverage is greater or equal 5% then the time at that point is stored and the loop ends
        if round(y[i], 2) >= t_lag_level:
            t_lag = x[i]
            t_lag_index = i
            break
    # if a lag time wasn't picked up auto assing the maximum
    if t_lag_index == None:
        t_lag=max_t_lag
        t_lag_index=0
    # If the lag time is huge, change the index we pass the slope fitter
    if t_lag_index>0.6*len(x):
        t_lag_index=0
    return t_lag,t_lag_index,max_index

# Get index for first data point 20% away from the max
def get_max_index(x,y,tolerance=0.2):
    max_index=-1
    max_SC=np.max(y)
    for i in range(len(y)):
        difference = np.absolute((y[i] - max_SC) / max_SC)
        if difference <= tolerance:
            max_index = i
            break
    if max_SC<100:
        max_index=len(y)+1
    return max_index

def interpolate_series(df,interp_interval=1):
    # Get index
    interval=df['time (s)'][1]-df['time (s)'][0]
    start=np.min(df['time (s)'])
    stop=np.max(df['time (s)'])+interval
    x=np.linspace(start,stop,100)
    y=np.interp(x,df['time (s)'],df['Zero Mean'])
    return x,y