"""Fill in a module description here"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/05_utils.ipynb.

# %% ../nbs/05_utils.ipynb 5
from __future__ import annotations
from fastcore.docments import *
from fastcore.utils import *

import pandas as pd
import numpy as np
from collections import Counter, defaultdict

import copy
import warnings

# %% auto 0
__all__ = ['restructureWeightsDataList', 'summarizeWeightsData', 'restructureWeightsDataList_multivariate',
           'summarizeWeightsData_multivariate', 'generateFinalOutput']

# %% ../nbs/05_utils.ipynb 7
def restructureWeightsDataList(weightsDataList, outputType = 'onlyPositiveWeights', y = None, scalingList = None, equalWeights = False):
    
    # CHECKS AND WARNINGS
    if not scalingList is None:
        
        if len(scalingList) > len(weightsDataList):
            warnings.warn("'scalingList' is longer than 'weightsDataList'")
            
        elif len(scalingList) > len(weightsDataList):
            raise ValueError("'scalingList' mustn't be shorter than 'weightsDataList'")
    
    #---
    
    if outputType == 'all':
        
        weightsDataListAll = list()
        
        for weights, indicesPosWeight in weightsDataList:
            weightsAll = np.zeros(len(y))
            weightsAll[indicesPosWeight] = weights
            weightsDataListAll.append(weightsAll)
        
        return weightsDataListAll
    
    #---
    
    elif outputType == 'onlyPositiveWeights':
        
        return weightsDataList
    
    #---
    
    elif outputType == 'onlyPositiveWeightsValues':
        
        weightsDataListNew = list()

        for i in range(len(weightsDataList)):
            weights, values = weightsDataList[i][0], y[weightsDataList[i][1]]
            
            if not scalingList is None:
                values = values * scalingList[i]
                
            weightsDataListNew.append((weights, values))
            
        return weightsDataListNew
    
    #---
    
    elif outputType == 'summarized':
        
        weightsDataListSummarized = list()

        for i in range(len(weightsDataList)):
            weightsPos, yWeightPos = weightsDataList[i][0], y[weightsDataList[i][1]]
            
            weightsSummarized, yUnique = summarizeWeightsData(weightsPos = weightsPos, 
                                                              yWeightPos = yWeightPos,
                                                              equalWeights = equalWeights)
            
            if not scalingList is None:
                yUnique = yUnique * scalingList[i]
                
            weightsDataListSummarized.append((weightsSummarized, yUnique))
            
        return weightsDataListSummarized
    
    #---
    
    elif outputType == 'cumulativeDistribution':
        
        distributionDataList = list()
        
        for i in range(len(weightsDataList)):
            weightsPos, yWeightPos = weightsDataList[i][0], y[weightsDataList[i][1]]
            
            indicesSort = np.argsort(yWeightPos)
            
            weightsPosSorted = weightsPos[indicesSort]
            yWeightPosSorted = yWeightPos[indicesSort]
            
            cumulativeProbs = np.cumsum(weightsPosSorted)
            
            if not scalingList is None:
                yWeightPosSorted = yWeightPosSorted * scalingList[i]
            
            distributionDataList.append((cumulativeProbs, yWeightPosSorted))
            
        return distributionDataList
    
    #---
    
    elif outputType == 'cumulativeDistributionSummarized':
        
        distributionDataList = list()
        
        for i in range(len(weightsDataList)):
            weightsPos, yWeightPos = weightsDataList[i][0], y[weightsDataList[i][1]]
            
            weightsSummarizedSorted, yPosWeightUniqueSorted = summarizeWeightsData(weightsPos = weightsPos, 
                                                                                   yWeightPos = yWeightPos,
                                                                                   equalWeights = equalWeights)
            
            cumulativeProbs = np.cumsum(weightsSummarizedSorted)
            
            if not scalingList is None:
                yPosWeightUniqueSorted = yPosWeightUniqueSorted * scalingList[i]
                
            distributionDataList.append((cumulativeProbs, yPosWeightUniqueSorted))
            
        return distributionDataList
    

# %% ../nbs/05_utils.ipynb 9
def summarizeWeightsData(weightsPos, yWeightPos, equalWeights = False):
    
    if equalWeights:
        
        counterDict = Counter(yWeightPos)
        yUniqueSorted = np.sort(list(counterDict.keys()))

        weightsSummarizedSorted = np.array([counterDict[value] / len(yWeightPos) for value in yUniqueSorted])
    
    else:
        duplicationDict = defaultdict(list)

        for i, yValue in enumerate(yWeightPos):
            duplicationDict[yValue].append(i)

        #---

        weightsSummarized = list()
        yUnique = list()

        for value, indices in duplicationDict.items():        

            weightsSummarized.append(weightsPos[indices].sum())
            yUnique.append(value)

        weightsSummarized, yUnique = np.array(weightsSummarized), np.array(yUnique)

        #---

        indicesSort = np.argsort(yUnique)
        weightsSummarizedSorted, yUniqueSorted = weightsSummarized[indicesSort], yUnique[indicesSort]
    
    return weightsSummarizedSorted, yUniqueSorted

# %% ../nbs/05_utils.ipynb 11
def restructureWeightsDataList_multivariate(weightsDataList, outputType = 'onlyPositiveWeights', y = None, scalingList = None, equalWeights = False):
    
    # CHECKS AND WARNINGS
    if not scalingList is None:
        
        if len(scalingList) > len(weightsDataList):
            warnings.warn("'scalingList' is longer than 'weightsDataList'")
            
        elif len(scalingList) > len(weightsDataList):
            raise ValueError("'scalingList' mustn't be shorter than 'weightsDataList'")
            
    #---
    
    if outputType == 'all':
        
        weightsDataListAll = list()
        
        for weights, indicesPosWeight in weightsDataList:
            weightsAll = np.zeros(len(y))
            weightsAll[indicesPosWeight] = weights
            weightsDataListAll.append(weightsAll)
        
        return weightsDataListAll
    
    #---
    
    elif outputType == 'onlyPositiveWeights':
        
        return weightsDataList
    
    #---
    
    elif outputType == 'summarized':
        
        weightsDataListSummarized = list()

        for i in range(len(weightsDataList)):
            weightsPos, yWeightPos = weightsDataList[i][0], y[weightsDataList[i][1]]
            
            weightsSummarized, yUnique = summarizeWeightsData_multivariate(weightsPos = weightsPos, 
                                                                           yWeightPos = yWeightPos,
                                                                           equalWeights = equalWeights)
            
            if not scalingList is None:
                yUnique = yUnique * scalingList[i]
                
            weightsDataListSummarized.append((weightsSummarized, yUnique))
            
        return weightsDataListSummarized
    

# %% ../nbs/05_utils.ipynb 13
def summarizeWeightsData_multivariate(weightsPos, yWeightPos, equalWeights = False):
    
    uniqueRes = np.unique(yWeightPos, return_counts = True, return_inverse = True, return_index = True, axis = 0)
    
    if equalWeights:
        
        weightsSummarizedSorted = np.array([uniqueRes[3][i] / len(yWeightPos) for i in range(len(uniqueRes[3]))])
        yUniqueSorted = uniqueRes[0]
        
    else:
        duplicationDict = defaultdict(list)
        for index, indexUnique in enumerate(uniqueRes[2]):
            duplicationDict[indexUnique].append(index)

        #---

        weightsSummarized = list()
        yUnique = list()

        for indexUnique, indices in duplicationDict.items():        

            weightsSummarized.append(weightsPos[indices].sum())
            yUnique.append(uniqueRes[0][indexUnique])

        weightsSummarized, yUnique = np.array(weightsSummarized), np.array(yUnique)

        #---

        indicesSort = np.argsort(yUnique)
        weightsSummarizedSorted, yUniqueSorted = weightsSummarized[indicesSort], yUnique[indicesSort]
    
    return weightsSummarizedSorted, yUniqueSorted

# %% ../nbs/05_utils.ipynb 15
def generateFinalOutput(dataOriginal, 
                        dataDecisions, 
                        targetVariable = 'demand', 
                        mergeOn = None, 
                        variablesToAdd = None, 
                        scaleBy = None, 
                        includeTraining = False, 
                        sortBy = None,
                        longFormat = False,
                        **kwargs):
    
    dataOriginal = dataOriginal.rename(columns = {targetVariable: 'actuals'})
    
    if not scaleBy is None:
        if not isinstance(scaleBy, str): 
            raise ValueError("'scaleBy' has to a string specifying a single feature to scale the target variable!")
        elif scaleBy in dataOriginal.columns:
            dataOriginal['actuals'] = dataOriginal['actuals'] * dataOriginal[scaleBy]
        else:
            raise ValueError(f"The specified feature {scaleBy} is not part of 'dataOriginal'!")
    
    #---
    
    # Adding additional data to the matrix dataDecisions
    # NOTE: This function is written to be useable for all datasets we currently use. 
    colsToAdd = ['id', 'sku_code_prefix', 'sku_code', 'SKU_API',
                 'actuals', 'revenue', 'label',
                 'adi', 'adi_sku', 'adi_product', 'cv2', 'cvDemand_sku', 'cvDemand_product']
    
    if isinstance(mergeOn, list):
        colsToAdd = colsToAdd + mergeOn
    else:
        colsToAdd.append(mergeOn)
    
    if isinstance(variablesToAdd, list):
        colsToAdd = colsToAdd + variablesToAdd
    else:
        colsToAdd.append(variablesToAdd)
        
    if isinstance(sortBy, list):
        colsToAdd = colsToAdd + sortBy
    else:
        colsToAdd.append(sortBy)
    
    colsToAdd = pd.Series(colsToAdd)
    colsToAdd = colsToAdd[colsToAdd.isin(dataOriginal.columns)] 
    colsToAdd = colsToAdd.unique()
    
    dataTestInfoToAdd = dataOriginal.loc[dataOriginal['label'] == 'test', colsToAdd].reset_index(drop = True)
    
    if not longFormat:

        if mergeOn is None:
            dataResults = pd.concat([dataTestInfoToAdd, dataDecisions.reset_index(drop = True)], axis = 1)
        else:
            dataResults = pd.merge(dataTestInfoToAdd, dataDecisions, on = mergeOn)

        #---
    
    #---
    
    else:
        
        dataDecisionsStacked = dataDecisions.stack().reset_index().set_index('level_0')
        dataDecisionsStacked.rename(columns = {'level_1': 'decisionType'}, inplace = True)
        
        dataDecisionsStacked.rename(columns = {0: 'decisions'}, inplace = True)
        dataDecisionsStacked.reset_index(drop = True, inplace = True)
        
        numberOfDecisionTypes = len(dataDecisionsStacked['decisionType'].unique())
        
        infoDuplicatedDf = dataTestInfoToAdd.loc[dataTestInfoToAdd.index.repeat(numberOfDecisionTypes)]
        infoDuplicatedDf.reset_index(drop = True, inplace = True)
        
        dataResults = pd.concat([infoDuplicatedDf, dataDecisionsStacked], axis = 1)
        
    #---
    
    infoToAdd = pd.DataFrame(kwargs, index = [0])
    infoToAdd['label'] = 'test'
    dataResults = pd.merge(dataResults, infoToAdd, on = 'label')
    
    #---
    
    if includeTraining:
        dataTrainInfoToAdd = dataOriginal.loc[dataOriginal['label'] == 'train', colsToAdd].reset_index(drop = True)
        dataResults = pd.concat([dataTrainInfoToAdd, dataResults], axis = 0).reset_index(drop = True)
            
    #---
    
    if not sortBy is None:
        
        if not all([sortByCol in dataResults.columns for sortByCol in sortBy]):
            raise ValueError("Columns specified by 'sortBy' must be part of 'dataOriginal'!")
        else:
            dataResults.sort_values(by = sortBy, axis = 0, inplace = True, ignore_index = True)
    
    return dataResults
