import pandas as pd
import numpy as np
import os
import glob
from skimage import io 
import javabridge
import bioformats
import vsi_metadata as v
import metric_functions as m


def fluorescence_time_series (filepath,interval=18,threshold=100,
                               csv_path='',stats_path='',store_csv=False,
                               zero_index_time=0,stats=False,show_linear=False,
                               t_lag_level=250,rescale='None',background='None',
                               zero_index=0,threshold_filter=True,vsi=True,
                               cycle_vm=True,meta_number=None,image_channel=1,
                               t_sample=1,t_cutoff='None'
                               ):
    
    # if a vsi file is specified then read in through vsi means rather than manually reading in tifs
    if vsi:
        # start javabridge
        if cycle_vm:
            javabridge.start_vm(class_path=bioformats.JARS)
        # read in metadata using bioformats and make ararys for t ans z slices
        metadata=v.extract_metadata(filepath,cycle_vm=False,meta_number=meta_number)
        metadata['cycle time']=float(metadata['cycle time'])/1000
        if endpoint:
            t_slices=[0]
            t_slices_scaled=[0]
        else:
            
            t_slices=np.arange(zero_index,metadata['size_T'])
                
            t_slices=t_slices[::t_sample]
            
            t_slices_scaled=(t_slices-zero_index)*float(metadata['cycle time'])*t_sample
            # command to analyze only so many steps of data 
            if t_cutoff != 'None':
                cutoff_bool=t_slices_scaled<t_cutoff
                t_slices_scaled=t_slices_scaled[cutoff_bool]
                t_slices=t_slices[cutoff_bool]
        z_slices=np.arange(0,metadata['size_Z'])
        mean = np.empty(len(t_slices))
        minimum = np.empty(len(t_slices))
        maximum = np.empty(len(t_slices))
        for i in range(len(t_slices)):
            # show_handler,not_shown,pic_pct=show_controller(i+1,pic_length,*not_shown)
            # read in image and convert to 8 bit
            if len(z_slices)==1:
                image=bioformats.load_image(path=filepath,t=t_slices[i],series=0)
                if len(np.shape(image))>2:
                    image=image[:,:,image_channel]
            else:
                image=max_projection(filepath,t_slices[i],z_slices,image_channel)
            mean[i] = np.mean(image)
            minimum[i] = np.min(image)
            maximum[i] = np.max(image)
    # Otherwise manually read in tifs 
    else: 
        # Boolean process to deterine whether or not tor
        former_path=os.getcwd()
        os.chdir(filepath)
        # Read sort in the tif files of a given pathway
        filenames=sorted(glob.glob('*.tif'))
        # read in the images and get the mean, min, and max then store as dataframe
        mean = np.empty(len(filenames))
        minimum = np.empty(len(filenames))
        maximum = np.empty(len(filenames))
        i=0
        for file in filenames:
            image = io.imread(file)
            mean[i] = np.mean(image)
            minimum[i] = np.min(image)
            maximum[i] = np.max(image)
            i += 1
        os.chdir(former_path)
    # Sometimes it makes sense to specify a index (time point) to subtract background by specifying an image. If no index is specified
    # then I make an autodetect function using a threshold filter
    if zero_index == 'None':
        if threshold_filter:
            zero_index = 0
            for i in range(len(mean)):
                if i == 0:
                    continue
                    if mean[i] > threshold:
                        zero_index = i
                        break
    else:
        zero_index=int(zero_index)
    # cut arrays using zero index value
    mean = mean[zero_index:]
    minimum = minimum[zero_index:]
    maximum = maximum[zero_index:]
    # rescale mean of image if specified
    if rescale!='None':
        mean=mean*rescale
        maximum=maximum*rescale
        minimum=minimum*rescale
    # subtract background. If a specific background in inputted and spec_background = True then it will use the specified value
    if background=='None':
        zero_mean = mean - mean[0]
    else:
        zero_mean = mean - background
    # generate time series data
    if vsi:
        time=t_slices_scaled[zero_index:]-t_slices_scaled[zero_index]
    else:
        time = np.linspace(zero_index_time, interval * len(mean), len(mean),endpoint=False)
    # store to dataframe for easy usage
    df = pd.DataFrame({'time (s)': time, 'Mean': mean, 'Zero Mean': zero_mean, 'Min': minimum, 'Max': maximum})
    # delte rows with saturated values
    df=df[df['Mean']<60000]
    if stats:
        f_metric_options=dict(show_linear=show_linear,interval=interval
                )
        try:
            t_lag_level
        except:
            pass
        else:
            f_metric_options['t_lag_level']=t_lag_level
        F_values = m.get_metrics(df, **f_metric_options)
    
    if stats:
        return df, F_values
    else:
        return df

# function that computes the max projection of images if they are z-stacks
def max_projection(path,t_slice,z_slices,image_channel):
    count=0
    for z in z_slices:
        if z==np.min(z_slices):
            test_img = bioformats.load_image(path=path, t=t_slice,z=z, series=0)
            shape=np.shape(test_img)
            img_array=np.zeros([shape[0],shape[1],len(z_slices)])
        img_loop=bioformats.load_image(path=path, t=t_slice,z=z, series=0)*65535
        if len(np.shape(img_loop))>2:
            img_loop=img_loop[:,:,image_channel]
        img_array[:,:,count]=img_loop
        count+=1
    max_intensity=np.amax(img_array,axis=2)
    return max_intensity

# controller that tells the return_area function to show a comparison of the thresholded function at set values in the 
def show_controller(count_pics,pic_length,*not_shown,pic_thresh=[20,50,90]):
    # cast not shown as list
    not_shown=list(not_shown)
    pic_pct = np.round(count_pics / pic_length * 100, 2)
    if pic_pct >= pic_thresh[0] and not_shown[0] == True:
        show_handler = True
        not_shown[0] = False
    elif pic_pct >= pic_thresh[1] and not_shown[1] == True:
        show_handler = True
        not_shown[1] = False
    elif pic_pct >= pic_thresh[2] and not_shown[2] == True:
        show_handler = True
        not_shown[2] = False
    else:
        show_handler = False
    return show_handler,not_shown,pic_pct
