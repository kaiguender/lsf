# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_levelSetKDEx_univariate.ipynb.

# %% ../nbs/01_levelSetKDEx_univariate.ipynb 4
from __future__ import annotations
from fastcore.docments import *
from fastcore.test import *
from fastcore.utils import *

import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

from collections import defaultdict, Counter, deque
import warnings

from sklearn.base import BaseEstimator
from sklearn.exceptions import NotFittedError
from .baseClasses import BaseLSx, BaseWeightsBasedEstimator
from .utils import restructureWeightsDataList

# %% auto 0
__all__ = ['LevelSetKDEx', 'generateBins', 'LevelSetKDEx_kNN', 'LevelSetKDEx_NN', 'getNeighbors', 'getNeighborsTest',
           'getKernelValues']

# %% ../nbs/01_levelSetKDEx_univariate.ipynb 7
class LevelSetKDEx(BaseWeightsBasedEstimator, BaseLSx):
    """
    `LevelSetKDEx` turns any point forecasting model into an estimator of the underlying conditional density.
    The name 'LevelSet' stems from the fact that this approach interprets the values of the point forecasts
    as a similarity measure between samples. The point forecasts of the training samples are sorted and 
    recursively assigned to a bin until the size of the current bin reaches `binSize` many samples. Then
    a new bin is created and so on. For a new test sample we check into which bin its point prediction
    would have fallen and interpret the training samples of that bin as the empirical distribution function
    of this test sample.    
    """
    
    def __init__(self, 
                 estimator, # Model with a .fit and .predict-method (implementing the scikit-learn estimator interface).
                 binSize: int=None, # Size of the bins created while running fit.
                 # Determines behaviour of method `getWeights`. If False, all weights receive the same  
                 # value. If True, the distance of the point forecasts is taking into account.
                 weightsByDistance: bool=False, 
                 ):
        
        super(BaseEstimator, self).__init__(estimator = estimator,
                                            binSize = binSize,
                                            weightsByDistance = weightsByDistance)

        self.yTrain = None
        self.yPredTrain = None
        self.indicesPerBin = None
        self.lowerBoundPerBin = None
        self.fitted = False
    
    #---
    
    def fit(self: LevelSetKDEx, 
            X: np.ndarray, # Feature matrix used by `estimator` to predict `y`.
            y: np.ndarray, # 1-dimensional target variable corresponding to the feature matrix `X`.
            ):
        """
        Fit `LevelSetKDEx` model by grouping the point predictions of the samples specified via `X`
        according to their value. Samples are recursively sorted into bins until each bin contains
        `binSize` many samples. For details, checkout the function `generateBins` which does the
        heavy lifting.
        """
        
        # Checks
        if self.binSize is None:
            raise ValueError("'binSize' must be specified to fit the LSx estimator!")
            
        if self.binSize > y.shape[0]:
            raise ValueError("'binSize' mustn't be bigger than the size of 'y'!")
        
        if X.shape[0] != y.shape[0]:
            raise ValueError("'X' and 'y' must contain the same number of samples!")
        
        # IMPORTANT: In case 'y' is given as a pandas.Series, we can potentially run into indexing 
        # problems later on.
        if isinstance(y, pd.Series):
            y = y.ravel()
        
        #---
        
        try:
            yPred = self.estimator.predict(X)
            
        except NotFittedError:
            try:
                self.estimator.fit(X = X, y = y)                
            except:
                raise ValueError("Couldn't fit 'estimator' with user specified 'X' and 'y'!")
            else:
                yPred = self.estimator.predict(X)
        
        #---
        
        indicesPerBin, lowerBoundPerBin = generateBins(binSize = self.binSize,
                                                       yPred = yPred)

        self.yTrain = y
        self.yPredTrain = yPred
        self.indicesPerBin = indicesPerBin
        self.lowerBoundPerBin = lowerBoundPerBin
        self.fitted = True
        
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
        
        # __annotations__ = BaseWeightsBasedEstimator.getWeights.__annotations__
        __doc__ = BaseWeightsBasedEstimator.getWeights.__doc__
        
        if not self.fitted:
            raise NotFittedError("This LevelSetKDEx instance is not fitted yet. Call 'fit' with "
                                 "appropriate arguments before trying to compute weights.")
        
        #---
        
        yPred = self.estimator.predict(X)
        
        binPerPred = np.searchsorted(a = self.lowerBoundPerBin, v = yPred, side = 'right') - 1
        neighborsList = [self.indicesPerBin[binIndex] for binIndex in binPerPred]
        
        #---
        
        if self.weightsByDistance:

            predDistances = [np.abs(self.yPredTrain[neighborsList[i]] - yPred[i]) for i in range(len(neighborsList))]

            weightsDataList = list()
            
            for i in range(X.shape[0]):
                distances = predDistances[i]
                distancesCloseZero = np.isclose(distances, 0)
                
                if np.any(distancesCloseZero):
                    indicesCloseZero = neighborsList[i][np.where(distancesCloseZero)[0]]
                    weightsDataList.append((np.repeat(1 / len(indicesCloseZero), len(indicesCloseZero)),
                                            indicesCloseZero))
                    
                else:                                 
                    inverseDistances = 1 / distances

                    weightsDataList.append((inverseDistances / inverseDistances.sum(), 
                                            np.array(neighborsList[i])))
            
            weightsDataList = restructureWeightsDataList(weightsDataList = weightsDataList, 
                                                         outputType = outputType, 
                                                         y = self.yTrain,
                                                         scalingList = scalingList,
                                                         equalWeights = False)
        
        else:
            weightsDataList = [(np.repeat(1 / len(neighbors), len(neighbors)), np.array(neighbors)) for neighbors in neighborsList]

            weightsDataList = restructureWeightsDataList(weightsDataList = weightsDataList, 
                                                         outputType = outputType, 
                                                         y = self.yTrain,
                                                         scalingList = scalingList,
                                                         equalWeights = True)
        
        return weightsDataList
    

# %% ../nbs/01_levelSetKDEx_univariate.ipynb 11
def generateBins(binSize: int, # Size of the bins of values of `yPred` being grouped together.
                 yPred: np.ndarray, # 1-dimensional array of predicted values.
                 ):
    "Used to generate the bin-structure used by `LevelSetKDEx` to compute density estimations."
    
    predIndicesSort = np.argsort(yPred)
    yPredSorted = yPred[predIndicesSort]

    currentBinSize = 0
    binIndex = 0
    trainIndicesLeft = len(yPred)
    indicesPerBin = defaultdict(list)
    lowerBoundPerBin = dict()
    
    for i in range(len(yPred)):
        
        if i == 0:
            lowerBoundPerBin[binIndex] = np.NINF
            
        currentBinSize += 1
        trainIndicesLeft -= 1

        indicesPerBin[binIndex].append(predIndicesSort[i])
        
        if trainIndicesLeft < binSize:
            indicesPerBin[binIndex].extend(predIndicesSort[np.arange(i+1, len(yPred), 1)])
            break

        if currentBinSize >= binSize and yPredSorted[i] < yPredSorted[i+1]:
            lowerBoundPerBin[binIndex + 1] = (yPredSorted[i] + yPredSorted[i+1]) / 2
            binIndex += 1
            currentBinSize = 0
           
    indicesPerBin = {binIndex: np.array(indices) for binIndex, indices in indicesPerBin.items()}
    
    lowerBoundPerBin = pd.Series(lowerBoundPerBin)
    lowerBoundPerBin.index.name = 'binIndex'
    
    return indicesPerBin, lowerBoundPerBin

# %% ../nbs/01_levelSetKDEx_univariate.ipynb 14
class LevelSetKDEx_kNN(BaseWeightsBasedEstimator, BaseLSx):
    """
     `LevelSetKDEx_kNN` turns any point predictor that has a .predict-method 
    into an estimator of the condititional density of the underlying distribution.
    The basic idea of each level-set based approach is to interprete the point forecast
    generated by the underlying point predictor as a similarity measure of samples.
    In the case of the `LevelSetKDEx_kNN` defined here, for every new samples
    'binSize'-many training samples are computed whose point forecast is closest
    to the point forecast of the new sample.
    The resulting empirical distribution of these 'nearest' training samples are 
    viewed as our estimation of the conditional distribution of each the new sample 
    at hand.
    
    NOTE: In contrast to the standard `LevelSetKDEx`, it is possible to apply
    `LevelSetKDEx_kNN` to arbitrary dimensional point predictors.
    """
    
    def __init__(self, 
                 estimator, # Model with a .fit and .predict-method (implementing the scikit-learn estimator interface).
                 binSize: int=None, # Size of the bins created while running fit.
                 # Determines behaviour of method `getWeights`. If False, all weights receive the same  
                 # value. If True, the distance of the point forecasts is taking into account.
                 weightsByDistance: bool=False, 
                 ):
        
        super(BaseEstimator, self).__init__(estimator = estimator,
                                            binSize = binSize,
                                            weightsByDistance = weightsByDistance)
        
        self.yTrain = None
        self.yPredTrain = None
        self.nearestNeighborsOnPreds = None
        self.fitted = False
        
    #---
    
    def fit(self: LevelSetKDEx, 
            X: np.ndarray, # Feature matrix used by `estimator` to predict `y`.
            y: np.ndarray, # 1-dimensional target variable corresponding to the feature matrix `X`.
            ):
        """
        Fit `LevelSetKDEx_kNN` model by applying the nearest neighbors algorithm to the point
        predictions of the samples specified by `X` based on `estimator`. 
        """
        
        # Checks
        if self.binSize is None:
            raise ValueError("'binSize' must be specified to fit the LSx estimator!")
            
        if self.binSize > y.shape[0]:
            raise ValueError("'binSize' mustn't be bigger than the size of 'y'!")
            
        if X.shape[0] != y.shape[0]:
            raise ValueError("'X' and 'y' must contain the same number of samples!")
            
        # IMPORTANT: In case 'y' is given as a pandas.Series, we can potentially run into indexing 
        # problems later on.
        if isinstance(y, pd.Series):
            y = y.ravel()
        
        #---
        
        try:
            yPred = self.estimator.predict(X)
        except NotFittedError:
            # warnings.warn("The object 'estimator' must have been fitted already!"
            #               "'estimator' will be fitted with 'X' and 'y' to enable point predicting!",
            #               stacklevel = 2)
            try:
                self.estimator.fit(X = X, y = y)                
            except:
                raise ValueError("Couldn't fit 'estimator' with user specified 'X' and 'y'!")
            else:
                yPred = self.estimator.predict(X)

        #---
        
        yPred_reshaped = np.reshape(yPred, newshape = (len(yPred), 1))
        
        nn = NearestNeighbors(algorithm = 'kd_tree')
        nn.fit(X = yPred_reshaped)

        #---

        self.yTrain = y
        self.yPredTrain = yPred
        self.nearestNeighborsOnPreds = nn
        self.fitted = True
        
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
        
        if not self.fitted:
            raise NotFittedError("This LevelSetKDEx_kNN instance is not fitted yet. Call 'fit' with "
                                 "appropriate arguments before trying to compute weights.")
            
        #---

        nn = self.nearestNeighborsOnPreds

        #---

        yPred = self.estimator.predict(X)   
        yPred_reshaped = np.reshape(yPred, newshape = (len(yPred), 1))

        distancesMatrix, neighborsMatrix = nn.kneighbors(X = yPred_reshaped, 
                                                         n_neighbors = self.binSize + 1)

        #---

        neighborsList = list(neighborsMatrix[:, 0:self.binSize])
        distanceCheck = np.where(distancesMatrix[:, self.binSize - 1] == distancesMatrix[:, self.binSize])
        indicesToMod = distanceCheck[0]

        for index in indicesToMod:
            distanceExtremePoint = np.absolute(yPred[index] - self.yPredTrain[neighborsMatrix[index, self.binSize-1]])

            neighborsByRadius = nn.radius_neighbors(X = yPred_reshaped[index:index + 1], 
                                                    radius = distanceExtremePoint, return_distance = False)[0]
            neighborsList[index] = neighborsByRadius

        #---
        
        if self.weightsByDistance:
            binSizesReal = [len(neighbors) for neighbors in neighborsList]
            binSizeMax = max(binSizesReal)
            
            distancesMatrix, neighborsMatrix = nn.kneighbors(X = yPred_reshaped, 
                                                             n_neighbors = binSizeMax)
            
            weightsDataList = list()
            
            for i in range(X.shape[0]):
                distances = distancesMatrix[i, 0:binSizesReal[i]]
                distancesCloseZero = np.isclose(distances, 0)
                
                if np.any(distancesCloseZero):
                    indicesCloseZero = neighborsMatrix[i, np.where(distancesCloseZero)[0]]
                    weightsDataList.append((np.repeat(1 / len(indicesCloseZero), len(indicesCloseZero)),
                                            indicesCloseZero))
                    
                else:                                 
                    inverseDistances = 1 / distances

                    weightsDataList.append((inverseDistances / inverseDistances.sum(), 
                                            np.array(neighborsList[i])))
            
            weightsDataList = restructureWeightsDataList(weightsDataList = weightsDataList, 
                                                         outputType = outputType, 
                                                         y = self.yTrain,
                                                         scalingList = scalingList,
                                                         equalWeights = False)
            
        else:
            weightsDataList = [(np.repeat(1 / len(neighbors), len(neighbors)), np.array(neighbors)) for neighbors in neighborsList]

            weightsDataList = restructureWeightsDataList(weightsDataList = weightsDataList, 
                                                         outputType = outputType, 
                                                         y = self.yTrain,
                                                         scalingList = scalingList,
                                                         equalWeights = True)

        return weightsDataList
      

# %% ../nbs/01_levelSetKDEx_univariate.ipynb 18
class LevelSetKDEx_NN(BaseWeightsBasedEstimator, BaseLSx):
    """
     `LevelSetKDEx_kNN` turns any point predictor that has a .predict-method 
    into an estimator of the condititional density of the underlying distribution.
    The basic idea of each level-set based approach is to interprete the point forecast
    generated by the underlying point predictor as a similarity measure of samples.
    In the case of the `LevelSetKDEx_kNN` defined here, for every new samples
    'binSize'-many training samples are computed whose point forecast is closest
    to the point forecast of the new sample.
    The resulting empirical distribution of these 'nearest' training samples are 
    viewed as our estimation of the conditional distribution of each the new sample 
    at hand.
    
    NOTE: In contrast to the standard `LevelSetKDEx`, it is possible to apply
    `LevelSetKDEx_kNN` to arbitrary dimensional point predictors.
    """
    
    def __init__(self, 
                 estimator, # Model with a .fit and .predict-method (implementing the scikit-learn estimator interface).
                 binSize: int=None, # Size of the bins created while running fit.
                 # Determines behaviour of method `getWeights`. If False, all weights receive the same  
                 # value. If True, the distance of the point forecasts is taking into account.
                 weightsByDistance: bool=False, 
                 ):
        
        super(BaseEstimator, self).__init__(estimator = estimator,
                                            binSize = binSize,
                                            weightsByDistance = weightsByDistance)
        
        self.yTrain = None
        self.yPredTrain = None
        self.nearestNeighborsOnPreds = None
        self.fitted = False
        
    #---
    
    def fit(self: LevelSetKDEx, 
            X: np.ndarray, # Feature matrix used by `estimator` to predict `y`.
            y: np.ndarray, # 1-dimensional target variable corresponding to the feature matrix `X`.
            ):
        """
        Fit `LevelSetKDEx_kNN` model by applying the nearest neighbors algorithm to the point
        predictions of the samples specified by `X` based on `estimator`. 
        """
        
        # Checks
        if self.binSize is None:
            raise ValueError("'binSize' must be specified to fit the LSx estimator!")
            
        if self.binSize > y.shape[0]:
            raise ValueError("'binSize' mustn't be bigger than the size of 'y'!")
            
        if X.shape[0] != y.shape[0]:
            raise ValueError("'X' and 'y' must contain the same number of samples!")
            
        # IMPORTANT: In case 'y' is given as a pandas.Series, we can potentially run into indexing 
        # problems later on.
        if isinstance(y, pd.Series):
            y = y.ravel()
        
        #---
        
        try:
            yPred = self.estimator.predict(X)
            
        except NotFittedError:
            try:
                self.estimator.fit(X = X, y = y)                
            except:
                raise ValueError("Couldn't fit 'estimator' with user specified 'X' and 'y'!")
            else:
                yPred = self.estimator.predict(X)

        #---
        
        neighborsDict, neighborsRemoved, neighborsAdded = getNeighbors(binSize = self.binSize,
                                                                       yPred = yPred)

        self.yTrain = y
        self.yPredTrain = yPred
        self.neighborsDictTrain = neighborsDict
        self._neighborsRemoved = neighborsRemoved
        self._neighborsAdded = neighborsAdded
        self._fitted = True
        
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
        
        if not self._fitted:
            raise NotFittedError("This LevelSetKDEx_kNN instance is not fitted yet. Call 'fit' with "
                                 "appropriate arguments before trying to compute weights.")
            
        #---
        
        yPred = self.estimator.predict(X)
        
        neighborsDictTest = getNeighborsTest(binSize = self.binSize,
                                             yPred = yPred,
                                             yPredTrain = self.yPredTrain,
                                             neighborsDictTrain = self.neighborsDictTrain)
        
        #---
        
        weightsDataList = getKernelValues(yPred = yPred,
                                          yPredTrain = self.yPredTrain,
                                          neighborsDictTest = neighborsDictTest,
                                          neighborsDictTrain = self.neighborsDictTrain,
                                          neighborsRemoved = self._neighborsRemoved,
                                          neighborsAdded = self._neighborsAdded,
                                          binSize = self.binSize,
                                          returnWeights = True)
        
        weightsDataList = restructureWeightsDataList(weightsDataList = weightsDataList, 
                                                     outputType = outputType, 
                                                     y = self.yTrain,
                                                     scalingList = scalingList,
                                                     equalWeights = True)

        return weightsDataList
      

# %% ../nbs/01_levelSetKDEx_univariate.ipynb 20
def getNeighbors(binSize: int, # Size of the bins of values of `yPred` being grouped together.
                 yPred: np.ndarray, # 1-dimensional array of predicted values.
                 ):
    "Used to generate the neighboorhoods used by `LevelSetKDEx` to compute density estimations."
    
    duplicationDict = defaultdict(list)
    counterDict = defaultdict(int)
    
    for index, value in enumerate(yPred):
        duplicationDict[value].append(index)
        counterDict[value] += 1
    
    yPredUnique = np.sort(list(duplicationDict.keys()))
    
    neighborsPerPred = dict()
    
    #---
    
    neighbors = deque()
    
    for k in range(len(yPredUnique)):
        
        if len(neighbors) < binSize:
            neighbors.extend(duplicationDict[yPredUnique[k]])
            
        else:
            neighborsMaxIter = k
            break
        
        if k == (len(yPredUnique) - 1):
            neighborsMaxIter = len(yPred)
            
    neighborsPerPred[yPredUnique[0]] = list(neighbors)
    
    #---
    
    neighborsRemoved = [0]
    neighborsAdded = [0]
    
    for i in range(1, len(yPredUnique)):
        
        removeCounter = 0
        addCounter = 0
        
        predCurrent = yPredUnique[i]
        
        #---
            
        # Check and Clean current neighborhood before starting the loop
            
        if len(neighbors) > binSize:
            
            checkNeeded = True
            while checkNeeded:
                
                distanceToMin = predCurrent - yPred[neighbors[0]]
                distanceToMax = yPred[neighbors[len(neighbors) - 1]] - predCurrent

                if distanceToMin > 0 and distanceToMin > distanceToMax:
                    countIdenticalMin = counterDict[yPred[neighbors[0]]]
                
                    if len(neighbors) - countIdenticalMin >= binSize:
                        removeCounter += countIdenticalMin

                        for p in range(countIdenticalMin):
                            neighbors.popleft()
                            
                    else:
                        checkNeeded = False
                else:
                    checkNeeded = False

        #---
        
        distanceToMin = predCurrent - yPred[neighbors[0]]
        distanceToMax = yPred[neighbors[len(neighbors) - 1]] - predCurrent

        for k in range(neighborsMaxIter, len(yPredUnique), 1):
            predNew = yPredUnique[k]
            distance = predNew - predCurrent 

            if len(neighbors) < binSize:
                neighbors.extend(duplicationDict[predNew])
                distanceToMax = yPred[neighbors[len(neighbors) - 1]] - predCurrent
                addCounter += counterDict[predNew]
                
            elif distance < distanceToMin:
                neighbors.extend(duplicationDict[predNew])
                addCounter += counterDict[predNew]
                
                countIdenticalMin = counterDict[yPred[neighbors[0]]]
                for p in range(countIdenticalMin): 
                    neighbors.popleft()
                    
                removeCounter += countIdenticalMin
                distanceToMin = predCurrent - yPred[neighbors[0]]
                distanceToMax = yPred[neighbors[len(neighbors) - 1]] - predCurrent

            elif distance == distanceToMin:
                neighbors.extend(duplicationDict[predNew])
                distanceToMax = yPred[neighbors[len(neighbors) - 1]] - predCurrent
                addCounter += counterDict[predNew]
                
            elif distance == distanceToMax:
                neighbors.extend(duplicationDict[predNew])
                addCounter += counterDict[predNew]
                
            else:
                neighborsMaxIter = k
                break

            # If we end up down here, it means that all train preds have sucessuflly been
            # added to the current neighborhood. For that reason, k has to be set to len(yPred)
            # in order to stop the code from starting the loop.
            if k == (len(yPredUnique) - 1):
                neighborsMaxIter = len(yPred)
        
        neighborsPerPred[predCurrent] = list(neighbors)
        neighborsRemoved.append(removeCounter)
        neighborsAdded.append(addCounter)
        
    #---
 
    return neighborsPerPred, np.array(neighborsRemoved), np.array(neighborsAdded)

# %% ../nbs/01_levelSetKDEx_univariate.ipynb 22
def getNeighborsTest(binSize: int, # Size of the bins of values of `yPred` being grouped together.
                     yPred: np.ndarray, # 1-dimensional array of predicted values.
                     yPredTrain: np.ndarray, # 1-dimensional array of predicted train values.
                     # Dict containing the neighbors of all train samples. Keys are the train predictions.
                     neighborsDictTrain: dict, 
                     ):
    "Used to generate the neighboorhoods used by `LevelSetKDEx` to compute density estimations."
    
    duplicationDict = defaultdict(list)
    counterDict = defaultdict(int)
    
    for index, value in enumerate(yPredTrain):
        duplicationDict[value].append(index)
        counterDict[value] += 1
    
    yPredTrainUnique = np.sort(list(duplicationDict.keys()))
    yPredUnique = np.unique(yPred)
    
    yPredTrainUniqueRanking = {value: index for index, value in enumerate(yPredTrainUnique)}
    
    trainIndicesClosest = np.searchsorted(a = yPredTrainUnique, v = yPredUnique, side = 'right') - 1
    
    # Needed if any yPred value is lower than all yPredTrain values
    trainIndicesClosest = np.clip(a = trainIndicesClosest, a_min = 0, a_max = None) 
    yPredTrainClosest = yPredTrainUnique[trainIndicesClosest]
    
    #---
    
    neighborsPerPred = dict()

    for i, predCurrent in enumerate(yPredUnique):
        
        neighbors = deque(neighborsDictTrain[yPredTrainClosest[i]])
        neighborsMaxIndex = yPredTrainUniqueRanking[yPredTrain[neighbors[len(neighbors) - 1]]]
        
        distanceToMin = predCurrent - yPredTrain[neighbors[0]]
        
        # Check and Clean current neighborhood before starting the loop
        if len(neighbors) > binSize:
            
            checkNeeded = True
            while checkNeeded:
                
                distanceToMin = predCurrent - yPredTrain[neighbors[0]]
                distanceToMax = yPredTrain[neighbors[len(neighbors) - 1]] - predCurrent

                if distanceToMin > 0 and distanceToMin > distanceToMax:
                    countIdenticalValuesLeftSide = counterDict[yPredTrain[neighbors[0]]]

                    if len(neighbors) - countIdenticalValuesLeftSide >= binSize:
                        for p in range(countIdenticalValuesLeftSide):
                            neighbors.popleft()
                    else:
                        checkNeeded = False
                else:
                    checkNeeded = False

        #---

        distanceToMin = predCurrent - yPredTrain[neighbors[0]]
        distanceToMax = yPredTrain[neighbors[len(neighbors) - 1]] - predCurrent

        for k in range(neighborsMaxIndex + 1, len(yPredTrainUnique), 1):
            predNew = yPredTrainUnique[k]
            distance = predNew - predCurrent 
                
            if len(neighbors) < binSize:
                neighbors.extend(duplicationDict[predNew])
                distanceToMax = yPredTrain[neighbors[len(neighbors) - 1]] - predCurrent

            elif distance < distanceToMin:
                neighbors.extend(duplicationDict[predNew])
                
                for p in range(counterDict[yPredTrain[neighbors[0]]]): 
                    neighbors.popleft()

                distanceToMin = predCurrent - yPredTrain[neighbors[0]]
                distanceToMax = yPredTrain[neighbors[len(neighbors) - 1]] - predCurrent

            elif distance == distanceToMin:
                neighbors.extend(duplicationDict[predNew])
                distanceToMax = yPredTrain[neighbors[len(neighbors) - 1]] - predCurrent

            elif distance == distanceToMax:
                neighbors.extend(duplicationDict[predNew])

            else:
                break
        
        neighborsPerPred[predCurrent] = list(neighbors)
        
    #---
 
    return neighborsPerPred

# %% ../nbs/01_levelSetKDEx_univariate.ipynb 24
def getKernelValues(yPred,
                    yPredTrain,
                    neighborsDictTest,
                    neighborsDictTrain,
                    neighborsRemoved,
                    neighborsAdded,
                    binSize,
                    returnWeights = True):
    
    duplicationDict = defaultdict(list)
    counterDict = defaultdict(int)
    
    for index, value in enumerate(yPredTrain):
        duplicationDict[value].append(index)
        counterDict[value] += 1
    
    yPredTrainUnique = np.sort(list(neighborsDictTrain.keys()))
    trainIndicesClosest = np.searchsorted(a = yPredTrainUnique, v = yPred, side = 'right') - 1
    
    # Needed if any yPred value is lower than all yPredTrain values
    trainIndicesClosest = np.clip(a = trainIndicesClosest, a_min = 0, a_max = None)
    
    #---
    
    kernelValuesList = list()
    
    for i in range(len(yPred)):
        
        trainIndexClosest = trainIndicesClosest[i]
        neighbors = neighborsDictTest[yPred[i]]
        sizeBin = len(neighbors)
        
        #---
        
        if trainIndexClosest + 1 <= len(yPredTrainUnique) - 1:
            neighborsTrainClosest = neighborsDictTrain[yPredTrainUnique[trainIndexClosest+1]]
            sharedNeighborsClosest = len(set(neighbors) & set(neighborsTrainClosest))
            
            if trainIndexClosest + 1 == len(yPredTrainUnique) - 1:
                kernelValuesRight = np.expand_dims(2 * sharedNeighborsClosest / (sizeBin + len(neighborsTrainClosest)), axis = 0)
                
            else:
                removeCum = np.concatenate([np.arange(1), neighborsRemoved[trainIndexClosest+2:len(yPredTrainUnique)]], axis = 0).cumsum()
                addCum = np.concatenate([np.arange(1), neighborsAdded[trainIndexClosest+2:len(yPredTrainUnique)]], axis = 0).cumsum()

                sharedNeighborsRight = np.clip(a = sharedNeighborsClosest - removeCum, a_min = 0, a_max = None)
                binSizesRight = len(neighborsTrainClosest) - removeCum + addCum

                kernelValuesRight = 2 * sharedNeighborsRight / (sizeBin + binSizesRight)
        
        else:
            kernelValuesRight = np.arange(0)
            
        #---
        
        # trainIndexClosest == -1 means that the test pred is lower than any train pred
        if trainIndexClosest >= 0:
            neighborsTrainClosest = neighborsDictTrain[yPredTrainUnique[trainIndexClosest]]
            sharedNeighborsClosest = len(set(neighbors) & set(neighborsTrainClosest))
            
            if trainIndexClosest == 0:
                kernelValuesLeft = np.expand_dims(2 * sharedNeighborsClosest / (sizeBin + len(neighborsTrainClosest)), axis = 0)
            
            else:
                neighborsRemovedFlip = np.flip(neighborsRemoved[1:trainIndexClosest+1])
                addCum = np.concatenate([np.arange(1), neighborsRemovedFlip], axis = 0).cumsum()

                neighborsAddedFlip = np.flip(neighborsAdded[1:trainIndexClosest+1])
                removeCum = np.concatenate([np.arange(1), neighborsAddedFlip], axis = 0).cumsum()

                sharedNeighborsLeft = np.clip(a = sharedNeighborsClosest - removeCum, a_min = 0, a_max = None)
                binSizesLeft = len(neighborsTrainClosest) - removeCum + addCum

                kernelValuesLeft = np.flip(2 * sharedNeighborsLeft / (sizeBin + binSizesLeft))
                    
        else:
            kernelValuesLeft = np.arange(0)

        #---
        
        kernelValuesUnique = np.concatenate([kernelValuesLeft, kernelValuesRight], axis = 0)
        kernelValuesList.append(kernelValuesUnique)
    
    #---
    
    kernelMatrixUnique = np.array(kernelValuesList)
    kernelMatrix = np.zeros(shape = (len(yPred), len(yPredTrain)))
    
    for index, predTrain in enumerate(yPredTrainUnique):
        kernelMatrix[:, duplicationDict[predTrain]] = kernelMatrixUnique[:, [index]]
    
    #---
    
    if returnWeights:
        weightsDataList = list()

        for i in range(len(yPred)):
            indices = np.where(kernelMatrix[i,:] > 0)[0]
            weights = kernelMatrix[i, indices]
            weights = weights / weights.sum()
            weightsDataList.append((weights, indices))
        
        return weightsDataList
    
    else:
        return kernelMatrix      
        
