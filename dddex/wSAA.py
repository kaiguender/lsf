# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/wSAA.ipynb.

# %% ../nbs/wSAA.ipynb 5
from __future__ import annotations
from fastcore.docments import *
from fastcore.test import *

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from .core import BaseWeightsBasedPredictor, restructureWeightsDataList

# %% auto 0
__all__ = ['RandomForestWSAA', 'SAA']

# %% ../nbs/wSAA.ipynb 8
class RandomForestWSAA(RandomForestRegressor, BaseWeightsBasedPredictor):
        
    def fit(self, X, Y):

        super(RandomForestRegressor, self).fit(X = X, y = Y)
        
        self.Y = Y
        self.leafIndicesTrain = self.apply(X)
        
    #---
    
    def getWeightsData(self, 
                       X: np.ndarray, # Feature matrix for whose rows conditional density estimates are computed.
                       outputType: 'all' | # Specifies structure of output.
                                   'onlyPositiveWeights' | 
                                   'summarized' | 
                                   'cumulativeDistribution' | 
                                   'cumulativeDistributionSummarized' = 'onlyPositiveWeights', 
                       scalingList: list | np.ndarray | None = None, # List or array with same size as self.Y containing floats being multiplied with self.Y.
                       ):
        
        leafIndicesDf = self.apply(X)
        
        weightsDataList = list()
        
        for leafIndices in leafIndicesDf:
            leafComparisonMatrix = (self.leafIndicesTrain == leafIndices) * 1
            nObsInSameLeaf = np.sum(leafComparisonMatrix, axis = 0)

            # It can happen that RF decides that the best strategy is to fit no tree at
            # all and simply average all results (happens when min_child_sample is too high, for example).
            # In this case 'leafComparisonMatrix' mustn't be averaged because there has been only a single tree.
            if len(leafComparisonMatrix.shape) == 1:
                weights = leafComparisonMatrix / nObsInSameLeaf
            else:
                weights = np.mean(leafComparisonMatrix / nObsInSameLeaf, axis = 1)
            
            weightsPosIndex = np.where(weights > 0)[0]
            
            weightsDataList.append((weights[weightsPosIndex], weightsPosIndex))
        
        #---
        
        weightsDataList = restructureWeightsDataList(weightsDataList = weightsDataList, 
                                                     outputType = outputType, 
                                                     Y = self.Y, 
                                                     scalingList = scalingList,
                                                     equalWeights = False)
        
        return weightsDataList
    
    #---
    
    def predict(self, 
                X: np.ndarray, # Feature matrix of samples for which an estimation of conditional quantiles is computed.
                probs: list | np.ndarray = [0.1, 0.5, 0.9], # Probabilities for which the estimated conditional p-quantiles are computed.
                outputAsDf: bool = False, # Output is either a dataframe with 'probs' as cols or a dict with 'probs' as keys.
                scalingList: list | np.ndarray | None = None, # List or array with same size as self.Y containing floats being multiplied with self.Y.
                ):
        
        quantileRes = super(BaseWeightsBasedPredictor, self).predict(X = X,
                                                                     probs = probs,
                                                                     outputAsDf = outputAsDf,
                                                                     scalingList = scalingList)
        
        return quantileRes
    
    #---
    
    def pointPredict(self, X):
        
        preds = super(RandomForestRegressor, self).predict(X)
        
        return preds
        

# %% ../nbs/wSAA.ipynb 10
class SAA(BaseWeightsBasedPredictor):
    
    def __init__(self):
        
        self.Y = None
    
    #---
    
    def fit(self, 
            Y: np.ndarray, # Target values which form the estimated density function based on the SAA algorithm.
            ):
        self.Y = Y
        
    #---
    
    def getWeightsData(self, 
                       X: np.ndarray, # Feature matrix for whose rows conditional density estimates are computed.
                       outputType: 'all' | # Specifies structure of output.
                                   'onlyPositiveWeights' | 
                                   'summarized' | 
                                   'cumulativeDistribution' | 
                                   'cumulativeDistributionSummarized' = 'onlyPositiveWeights', 
                       scalingList: list | np.ndarray | None = None, # List or array with same size as self.Y containing floats being multiplied with self.Y.
                       ):
        
        if X is None:
            neighborsList = [np.arange(len(self.Y))]
        else:
            neighborsList = [np.arange(len(self.Y)) for i in range(X.shape[0])]
        
        # weightsDataList is a list whose elements correspond to one test prediction each. 
        weightsDataList = [(np.repeat(1 / len(neighbors), len(neighbors)), np.array(neighbors)) for neighbors in neighborsList]

        weightsDataList = restructureWeightsDataList(weightsDataList = weightsDataList, 
                                                     outputType = outputType, 
                                                     Y = self.Y,
                                                     scalingList = scalingList,
                                                     equalWeights = True)
        
        return weightsDataList
    
