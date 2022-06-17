import cv2 
from skimage import exposure 
# Function that uses crop function to get bounds of the image
def get_bounds(img,scale=0.4):
    # resize image so it fits on screen when cropping
    convert_img=np.round(img*255/np.max(img),0)
    convert_img=convert_img.astype(np.uint8)
    eq_hist=exposure.equalize_hist(convert_img)
    dims = list(np.shape(img))
    dims = [float(d) for d in dims]
    adj_dims = [int(np.rint(scale * d)) for d in dims]
    adj_dims = tuple(adj_dims)
    img_scale = cv2.resize(eq_hist, dsize=adj_dims, interpolation=cv2.INTER_CUBIC)
    # crop image and return the bounds
    bounds = crop_img(img_scale, get_bounds=True)
    bounds=list(bounds) # convert to list for operations
    # rescale bounds based on rescale factor 
    for i in range(len(bounds)):
        bounds [i] = int(np.rint(bounds[i]/scale))
    return bounds
 
# Function for cropping image 
def crop_img(img,get_bounds=False,scale=1):
    # Select ROI
    r = cv2.selectROI(img)
    cv2.destroyAllWindows()
    if get_bounds==True:
        return r
    else:
        # Crop image
        im_crop = img[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]
        return im_crop    
