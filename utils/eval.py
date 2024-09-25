"""
It performs data-based evaluation
"""

import numpy as np
import cv2
from sklearn.metrics import confusion_matrix
import os
import pandas as pd

import warnings
warnings.filterwarnings("ignore")

# Chronic wound dataset directory
dir_label = r'.\azh_wound_care_center_dataset_patches\test\labels' # label directory
dir_pred = r'.\predictions\OldDFU' # prediction directory

HARD_LINE = True

names = os.listdir(dir_label)

stp, stn, sfp, sfn = 0, 0, 0, 0

ep = 1e-6

save_dir_pred = r'.\predictions'

# Create dataframe to store records
df = pd.DataFrame(index=[], columns = [
    'Name', 'Accuracy', 'Specificity', 'iou', 'Precision', 'Recall', 'Dice'], dtype='object')

# Create dataframe to store data-based record
df_data = pd.DataFrame(index=[], columns = [
    'Name', 'type', 'Accuracy', 'Specificity', 'iou', 'Precision', 'Recall', 'Dice', 'stp', 'stn', 'sfp', 'sfn'], dtype='object')

for i, name in enumerate(names):

    # image = cv2.imread(os.path.join(dir_im, name))[:,:,::-1]
    gt_mask = cv2.imread(os.path.join(dir_label, name), 0)

    # Note: Image shape: torch.Size([1, 3, 512, 512]) and mask shape: torch.Size([1, 1, 512, 512])

    pr_mask = cv2.imread(os.path.join(dir_pred, name), 0)

    # Move to CPU and convert to numpy
    gt_mask = np.squeeze(gt_mask)
    pred = np.squeeze(pr_mask)

    # Calculate accuracy, specificity, iou, precision, recall, and dice
    flat_mask = np.squeeze(gt_mask).flatten()
    flat_pred = np.squeeze(pred).flatten()
    
    # Calculate tp, fp, tn, fn
    unq_mask_val = np.unique(flat_mask) # unique values in the mask. For binary image, it should be 0 and 1
    
    'Case I: If there is no GT pixels in the image'
    if len(unq_mask_val)==1 and unq_mask_val==0: # Only one unique mask value and it is zero
        
        'Case I.a: If both GT and prediction are black' 
        if np.array_equal(flat_mask, flat_pred):
            # Calculate metrics for image-based evaluation. This time consider background as y_true. 
            acc, sp, p, r, dice, iou = 100, 100, 100, 100, 100, 100
            print("Img # {:1s}, Image {:1s}: acc: {:3f}, sp: {:3f}, iou: {:3f}, p: {:3f}, r: {:3f}, dice: {:3f}".format(str(i+1), name, acc, sp, iou, p, r, dice))
                        
            # Calculate the confusion matrix for data-based evaluation
            # Only tn will be counted. All others will be zero. Because the GT and the prediction
            # both have 0 pixels only. So, everything is truly negative.
            tn, fp, fn, tp = len(flat_mask), 0, 0, 0
   
        else:
            'Case I.b: If GT is black, but prediction not'
            if HARD_LINE:
                # If HARD_LINE is True, then all metrics will be set to 0s.
                
                # Calculate metrics for image-based evaluation
                acc, sp, p, r, dice, iou = 0, 0, 0, 0, 0, 0
                
                # Calculate confusion matrix for data-based evaluation
                tp, fn = 0, 0
                fp = np.count_nonzero(flat_pred) # no. of non-zero pixels
                tn = len(flat_pred) - fp # no. of zero intensity pixels
                
            else:
                # If HARD_LINE is False, then metrics will be calculated considering
                # background pixels as y_true. 
                
                # Calculate metrics for image-based evaluation. 
                # This time consider background as y_true. 
                # Invert (logical NOT) GT and prediction, meaning background will be considered as foreground now.
                invt_flat_mask = np.logical_not(flat_mask) * 1
                invt_flat_pred = np.logical_not(flat_pred) * 1
                
                itn, ifp, ifn, itp = confusion_matrix(invt_flat_mask, invt_flat_pred).ravel()
                
                # Calculate metrics for image-based evaluation 
                acc = ((itp + itn)/(itp + itn + ifn + ifp))*100  
                sp = (itn/(itn + ifp + ep))*100
                p = (itp/(itp + ifp + ep))*100
                r = (itp/(itp + ifn + ep))*100
                dice = 0#(2 * itp / (2 * itp + ifp + ifn))*100
                iou = (itp/(itp + ifp + ifn + ep)) * 100
    
                print("Img # {:1s}, Image {:1s}: acc: {:3f}, sp: {:3f}, iou: {:3f}, p: {:3f}, r: {:3f}, dice: {:3f}".format(str(i+1), name, acc, sp, iou, p, r, dice))
                
                # Calculate the confusion matrix for data-based evaluation
                # Do not do inversion (logical NOT). There will be some fp and tn. tp and fn will be 0.
                tn, fp, fn, tp = confusion_matrix(flat_mask, flat_pred).ravel()
    
    else:
        'Case II: If there is some GT pixels in the image'
        tn, fp, fn, tp = confusion_matrix(flat_mask, flat_pred).ravel()
        
        # Calculate metrics
        acc = ((tp + tn)/(tp + tn + fn + fp))*100  
        sp = (tn/(tn + fp + ep))*100
        p = (tp/(tp + fp + ep))*100
        r = (tp/(tp + fn + ep))*100
        dice = (2 * tp / (2 * tp + fp + fn))*100
        iou = (tp/(tp + fp + fn + ep)) * 100
        print("Img # {:1s}, Image {:1s}: acc: {:3f}, sp: {:3f}, iou: {:3f}, p: {:3f}, r: {:3f}, dice: {:3f}".format(str(i+1), name, acc, sp, iou, p, r, dice))
   
    
    # Keep adding tp, tn, fp, and fn
    stp += tp
    stn += tn
    sfp += fp
    sfn += fn

    # Add to dataframe
    tmp = pd.Series([name, acc, sp, iou, p, r, dice], index=['Name', 'Accuracy', 'Specificity', 'iou', 'Precision', 'Recall', 'Dice'])
    df = df.append(tmp, ignore_index = True)

df.to_csv(os.path.join(save_dir_pred, 'result_best_model.csv'), index=False)

print("Mean Accuracy: ", df["Accuracy"].mean())
print("Mean Specificity: ", df["Specificity"].mean())
print('Mean IoU: ', df['iou'].mean())
print("Mean precision: ", df["Precision"].mean())
print("Mean recall: ", df["Recall"].mean())
print("Mean dice: ", df["Dice"].mean())    

siou = (stp/(stp + sfp + sfn + ep))*100
sprecision = (stp/(stp + sfp + ep))*100
srecall = (stp/(stp + sfn + ep))*100
sdice = (2 * stp / (2 * stp + sfp + sfn))*100

print('siou:', siou)
print('sprecision:', sprecision)
print('srecall:', srecall)
print('sdice:', sdice)

# Save data-based result in a text file 
with open(os.path.join(save_dir_pred, 'result_data_based_best_model.txt'), 'w') as f:
    print(f'siou = {siou}', file=f)
    print(f'sprecision = {sprecision}', file=f)
    print(f'srecall = {srecall}', file=f)
    print(f'sdice = {sdice}', file=f)
