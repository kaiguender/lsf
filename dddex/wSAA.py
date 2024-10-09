"""Module description for wSAA classes"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_wSAA.ipynb.

# %% ../nbs/03_wSAA.ipynb 5
from __future__ import annotations
from fastcore.docments import *
from fastcore.test import *
from fastcore.utils import *

import pandas as pd
import numpy as np
import copy
from collections import defaultdict

from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
from sklearn.base import MetaEstimatorMixin
from lightgbm.sklearn import LGBMModel
from .baseClasses import BaseWeightsBasedEstimator
from .utils import restructureWeightsDataList, restructureWeightsDataList_multivariate

# %% auto 0
__all__ = ['RandomForestWSAA', 'RandomForestWSAA_LGBM', 'SampleAverageApproximation']

# %% ../nbs/03_wSAA.ipynb 7
class RandomForestWSAA(RandomForestRegressor, BaseWeightsBasedEstimator):
    
    def fit(self, 
            X: np.ndarray, # Feature matrix
            y: np.ndarray, # Target values
            **kwargs):

        super().fit(X = X, 
                    y = y, 
                    **kwargs)
        
        self.yTrain = y
        
        self.leafIndicesTrain = self.apply(X)
    
    #---
    
    def getWeights(self, 
                   X: np.ndarray, # Feature matrix for which conditional density estimates are computed.
                   # Specifies structure of the returned density estimates. One of: 
                   # 'all', 'onlyPositiveWeights', 'summarized', 'cumDistribution', 'cumDistributionSummarized'
                   outputType: str='onlyPositiveWeights', 
                   # Optional. List with length X.shape[0]. Values are multiplied to the estimated 
                   # density of each sample for scaling purposes.
                   scalingList: list=None, 
                   ) -> list: # List whose elements are the conditional density estimates for the samples specified by `X`.
        
        __doc__ = BaseWeightsBasedEstimator.getWeights.__doc__
        
        #---
        
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

        # Check if self.yTrain is a 2D array with more than one column.
        if len(self.yTrain.shape) > 1:
            if self.yTrain.shape[1] > 1:

                if not outputType in ['all', 'onlyPositiveWeights', 'summarized']:
                    raise ValueError("outputType must be one of 'all', 'onlyPositiveWeights', 'summarized' for multivariate y.")
                
                weightsDataList = restructureWeightsDataList_multivariate(weightsDataList = weightsDataList, 
                                                                        outputType = outputType, 
                                                                        y = self.yTrain, 
                                                                        scalingList = scalingList,
                                                                        equalWeights = False) 
            
        else:
            weightsDataList = restructureWeightsDataList(weightsDataList = weightsDataList, 
                                                        outputType = outputType, 
                                                        y = self.yTrain, 
                                                        scalingList = scalingList,
                                                        equalWeights = False)
            
        
                

        return weightsDataList
    
    #---
    
    def predict(self: BaseWeightsBasedEstimator, 
                X: np.ndarray, # Feature matrix for which conditional quantiles are computed.
                probs: list, # Probabilities for which quantiles are computed.
                outputAsDf: bool=True, # Determines output. Either a dataframe with probs as columns or a dict with probs as keys.
                # Optional. List with length X.shape[0]. Values are multiplied to the predictions
                # of each sample to rescale values.
                scalingList: list=None, 
                ): 
        
        __doc__ = BaseWeightsBasedEstimator.predict.__doc__
        
        return super(MetaEstimatorMixin, self).predict(X = X,
                                                       probs = probs, 
                                                       scalingList = scalingList)
    
    #---
    
    def pointPredict(self,
                     X: np.ndarray, # Feature Matrix
                     **kwargs):
        """Original `predict` method to generate point forecasts"""
        
        return super().predict(X = X,
                               **kwargs)


# %% ../nbs/03_wSAA.ipynb 9
class RandomForestWSAA_LGBM(LGBMRegressor, BaseWeightsBasedEstimator):
    
    def fit(self, 
            X: np.ndarray, # Feature matrix
            y: np.ndarray, # Target values
            **kwargs):

        super().fit(X = X, 
                    y = y, 
                    **kwargs)
        
        self.yTrain = y
        
        self.leafIndicesTrain = self.pointPredict(X, pred_leaf = True)
    
    #---
    
    def getWeights(self, 
                   X: np.ndarray, # Feature matrix for which conditional density estimates are computed.
                   # Specifies structure of the returned density estimates. One of: 
                   # 'all', 'onlyPositiveWeights', 'summarized', 'cumDistribution', 'cumDistributionSummarized'
                   outputType: str='onlyPositiveWeights', 
                   # Optional. List with length X.shape[0]. Values are multiplied to the estimated 
                   # density of each sample for scaling purposes.
                   scalingList: list=None, 
                   ) -> list: # List whose elements are the conditional density estimates for the samples specified by `X`.
        
        __doc__ = BaseWeightsBasedEstimator.getWeights.__doc__
        
        #---
        
        leafIndicesDf = self.pointPredict(X, pred_leaf = True)
        
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
                                                     y = self.yTrain, 
                                                     scalingList = scalingList,
                                                     equalWeights = False)

        return weightsDataList
    
    #---
    
    def predict(self: BaseWeightsBasedEstimator, 
                X: np.ndarray, # Feature matrix for which conditional quantiles are computed.
                probs: list, # Probabilities for which quantiles are computed.
                outputAsDf: bool=True, # Determines output. Either a dataframe with probs as columns or a dict with probs as keys.
                # Optional. List with length X.shape[0]. Values are multiplied to the predictions
                # of each sample to rescale values.
                scalingList: list=None, 
                ): 
        
        __doc__ = BaseWeightsBasedEstimator.predict.__doc__
        
        return super(LGBMModel, self).predict(X = X,
                                             probs = probs, 
                                             scalingList = scalingList)
    
    #---
    
    def pointPredict(self,
                     X: np.ndarray, # Feature Matrix
                     **kwargs):
        """Original `predict` method to generate point forecasts"""
        
        return super().predict(X = X,
                               **kwargs)


# %% ../nbs/03_wSAA.ipynb 11
class SampleAverageApproximation(BaseWeightsBasedEstimator):
    """SAA is a featureless approach that assumes the density of the target variable is given
    by assigning equal probability to each historical observation of said target variable."""
    
    def __init__(self):
        
        self.yTrain = None
        
    #---
        
    def __str__(self):
        return "SAA()"
    __repr__ = __str__ 
    
    #---
    
    def fit(self: SAA, 
            y: np.ndarray, # Target values which form the estimated density function based on the SAA algorithm.
            ):
        self.yTrain = y
    
    #---
    
    def getWeights(self, 
                   X: np.ndarray=None, # Feature matrix for which conditional density estimates are computed.
                   # Specifies structure of the returned density estimates. One of: 
                   # 'all', 'onlyPositiveWeights', 'summarized', 'cumDistribution', 'cumDistributionSummarized'
                   outputType: str='onlyPositiveWeights', 
                   # Optional. List with length X.shape[0]. Values are multiplied to the estimated 
                   # density of each sample for scaling purposes.
                   scalingList: list=None, 
                   ) -> list: # List whose elements are the conditional density estimates for the samples specified by `X`.
        
        __doc__ = BaseWeightsBasedEstimator.getWeights.__doc__
        
        # If no scaling is necessary, we can simply compute the data of the weights for a single observation and
        # then simply duplicate it.
        if (X is None) or (scalingList is None) or (outputType == 'onlyPositiveWeights'):
            
            neighborsList = [np.arange(len(self.yTrain))]
            weightsDataList = [(np.repeat(1 / len(neighbors), len(neighbors)), np.array(neighbors)) for neighbors in neighborsList]
            
            weightsDataList = restructureWeightsDataList(weightsDataList = weightsDataList, 
                                                         outputType = outputType, 
                                                         y = self.yTrain,
                                                         scalingList = scalingList,
                                                         equalWeights = True)
            
            if not X is None:
                weightsDataList = weightsDataList * X.shape[0]
        
        else:
            
            neighborsList = [np.arange(len(self.yTrain))] * X.shape[0]

            weightsDataList = [(np.repeat(1 / len(neighbors), len(neighbors)), np.array(neighbors)) for neighbors in neighborsList]

            weightsDataList = restructureWeightsDataList(weightsDataList = weightsDataList, 
                                                         outputType = outputType, 
                                                         y = self.yTrain,
                                                         scalingList = scalingList,
                                                         equalWeights = True)

        return weightsDataList
    
    #---
    
    def predict(self: SampleAverageApproximation, 
                X: np.ndarray, # Feature matrix for which conditional quantiles are computed.
                probs: list, # Probabilities for which quantiles are computed.
                # Optional. List with length X.shape[0]. Values are multiplied to the predictions
                # of each sample to rescale values.
                scalingList: list=None, 
                ) -> np.ndarray: 
        
        """
        Predict p-quantiles based on a reweighting of the empirical distribution function.
        In comparison to all other weights-based approaches, SAA only needs to compute
        the quantile predictions for one observation and then simply duplicate them.
        """
        
        
        # CHECKS
        if isinstance(probs, int) or isinstance(probs, float):
            if probs >= 0 and probs <= 1:
                probs = [probs]
            else:
                raise ValueError("The values specified via 'probs' must lie between 0 and 1!")           
                 
        if any([prob > 1 or prob < 0 for prob in probs]):
            raise ValueError("The values specified via 'probs' must lie between 0 and 1!")
            
        try:
            probs = np.array(probs)
        except:
            raise ValueError("Can't convert `probs` to 1-dimensional array.")
        
        #---

        distributionData = self.getWeights(X = None,
                                           outputType = 'cumulativeDistribution',
                                           scalingList = None)        

        # A tolerance term of 10^-8 is substracted from prob to account for rounding errors due to numerical precision.
        quantileIndices = np.searchsorted(a = distributionData[0][0], v = probs - 10**-8, side = 'left')
        quantiles = distributionData[0][1][quantileIndices]
        
        quantilesDf = pd.DataFrame([quantiles])
        quantilesDf.columns = probs
        
        quantilesDf_duplicated = pd.concat([quantilesDf] * X.shape[0], axis = 0).reset_index(drop = True)
        
        if not scalingList is None:
            quantilesDf_duplicated = (quantilesDf_duplicated.T * np.array(scalingList)).T
        
        return quantilesDf_duplicated
    
