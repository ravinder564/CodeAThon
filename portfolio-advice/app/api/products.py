from app.api import bp
import pandas as pd
import numpy as np
import os
from scipy.spatial.distance import cosine
from scipy.spatial.distance import hamming

basedir = os.path.abspath(os.path.dirname(__file__))
print(basedir)
models = pd.read_csv(".\\app\\api\models.csv", index_col='model_id')
products = pd.read_csv('.\\app\\api\equities.csv',index_col='Symbol')
holdings = pd.read_csv('.\\app\\api\model_holdings.csv', index_col=0)

df = models.drop(['account_name','model_name'],axis=1)
df = df.drop(df.columns[0], axis=1)
df = df.dropna()
df.volatility = df.volatility.round(2)
model_json = '{"inv_horizon":2.0,"inv_obj_least_imp":0.0,"inv_obj_most_imp":2.0,"inv_obj_some_imp":0.0,"inv_obj_very_imp":4.0,"investment_amt":745791.0,"liquidity_need":2.0,"primary_fin_need":7.0,"risk_profile":2.0,"risk_tolerance":0.0,"volatility":13.94}'
products = products.drop(products.columns[0], axis=1)
modelProductRatingMatrix = pd.pivot_table(holdings, values='percent', index=['model_id'],columns=['product_id'])

def findSimilarModel(model_json, df):
    input_model = pd.read_json(model_json, typ='series')
    input_model_df = input_model.to_frame().transpose()
    prev_similarity = 0
    final_ind = 0
    model_id = 0
    for i in range(len(df)) : 
        similarity = cosine(input_model_df.values,df.iloc[i,:])
        if(similarity <= prev_similarity):
            prev_similarity = similarity
            model_id = i
    return model_id

def productMeta(symbol):
    symbol = symbol
    name = products.at[symbol,"Name"]
    sector = products.at[symbol,"Sector"]
    close_price = products.at[symbol,"close_price"]
    risk_score = products.at[symbol,"risk_score"]
    L2 = products.at[symbol,"L2"]
    return symbol, name, sector, close_price, risk_score, L2

def favProducts(model_id, N):
    productRatings = holdings[holdings['model_id']==model_id]
    sortedRatings = pd.DataFrame.sort_values(productRatings,['percent'], ascending=[0])[:N]
    print(sortedRatings)
    sortedRatings['title'] = sortedRatings["product_id"].apply(productMeta)
    return sortedRatings


def distance(model1, model2):
    try:
        model1Ratings = modelProductRatingMatrix.transpose()[model1]
        #print(model1Ratings)
        model2Ratings = modelProductRatingMatrix.transpose()[model2]
        #print(model1Ratings)
        distance = hamming(model1Ratings,model2Ratings)
    except: 
        distance = np.NaN
    return distance

def nearestNeighbors(model_id, K=10):
    allModels = pd.DataFrame(modelProductRatingMatrix.index)
    allModels = allModels[allModels.model_id != model_id]
    allModels['distance'] = allModels['model_id'].apply(lambda x: distance(model_id, x))
    KnearestModels = allModels.sort_values(['distance'], ascending=True).index[:K]
    print(KnearestModels)
    return KnearestModels

def topNProducts(model_json, N=10):
    model_id = findSimilarModel(model_json, df)
    KnearestModels = nearestNeighbors(model_id)
    NNRatings = modelProductRatingMatrix[modelProductRatingMatrix.index.isin(KnearestModels)]
    avgRating = NNRatings.apply(np.nanmean).dropna()
    topNProducts = avgRating.sort_values(ascending=False).index[:N]
    return pd.Series(topNProducts)

@bp.route('/users', methods=['GET'])
def get_users():
    result = topNProducts(model_json,10)
    result_json = result.to_json(orient='records')
    return result_json    

