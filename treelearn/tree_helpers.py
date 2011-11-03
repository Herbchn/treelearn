# TreeLearn
#
# Copyright (C) Capital K Partners
# Author: Alex Rubinsteyn
# Contact: alex [at] capitalkpartners [dot] com 
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.


import numpy as np 
import scipy
import scipy.weave 


# some sklearn classifiers leave behind large data members after fitting
# which make serialization a pain--- clear those fields 
def clear_sklearn_fields(clf):
    if hasattr(clf, 'label_'):
        clf.label_ = None
    if hasattr(clf, 'sample_weight'):
        clf.sample_weight = None 
    

def midpoints(x):
    return (x[1:] + x[:-1])/2.0
    
def majority(labels, classes=None): 
    if classes is None: 
        classes = np.unique(labels)
    votes = np.zeros(len(classes))
    for i, c in enumerate(classes):
        votes[i] = np.sum(labels == c)
    majority_idx = np.argmax(votes)
    return classes[majority_idx] 


def slow_gini(classes, labels):
    sum_squares = 0.0
    n = len(labels)
    n_squared = float(n * n)
    for c in classes:
        count = np.sum(labels == c)
        p_squared = count*count / n_squared
        sum_squares += p_squared
    return 1 - sum_squares 

def slow_eval_split(classes, left_labels, right_labels): 
    left_score = slow_gini(classes, left_labels)
    right_score = slow_gini(classes, right_labels)    
    n_left = len(left_labels)
    n_right = len(right_labels)
    n = float(n_left+n_right)
    
    combined_score = (n_left/n)*left_score + (n_right/n)*right_score 
    return combined_score 

inline = scipy.weave.inline 
def gini(classes, labels): 
    code = """
        int num_classes = Nclasses[0]; 
        int n = Nlabels[0];
        float sum_squares = 0.0f; 
        for (int class_index = 0; class_index < num_classes; ++class_index) { 
            int c = classes[class_index]; 
            int count = 0; 
            for (int i = 0; i < n; ++i) { 
                if (labels[i] == c) { ++count; } 
            }
            float p = ((float) count) / n; 
            sum_squares += p * p; 
        }
        return_val = 1.0f - sum_squares; 
    """
    return inline(code, ['classes', 'labels'], local_dict=None, verbose=2)

    
def eval_gini_split(classes, left_labels, right_labels): 
    code = """
        int num_classes = Nclasses[0]; 
        int nleft = Nleft_labels[0];
        int nright = Nright_labels[0]; 
        
        float left_sum_squares = 0.0f; 
        float right_sum_squares = 0.0f; 
        
        for (int class_index = 0; class_index < num_classes; ++class_index) { 
            int c = classes[class_index]; 
            int count = 0; 
            
            for (int i = 0; i < nleft; ++i) { 
                if (left_labels[i] == c) { ++count; } 
            }
            float p = ((float) count) / nleft; 
            left_sum_squares += p * p; 
            
            count = 0; 
            for (int i = 0; i < nright; ++i) { 
                if (right_labels[i] == c) { ++count; } 
            }
            p = ((float) count) / nright; 
            right_sum_squares += p*p; 
            
        }
        float left_gini = 1.0f - left_sum_squares; 
        float right_gini = 1.0f - right_sum_squares; 
        float total = (float) (nleft + nright);
        float left_weight = nleft / total; 
        float right_weight = nright / total; 
         
        return_val = left_weight * left_gini + right_weight  * right_gini; 
    """
    return inline(code, ['classes', 'left_labels', 'right_labels'], \
        local_dict=None, verbose=2)
