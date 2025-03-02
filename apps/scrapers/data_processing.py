import pandas as pd
import numpy as np
from sklearn.neighbors import LocalOutlierFactor

def clean_deal_data(raw_data):
    # Convert to DataFrame
    df = pd.DataFrame(raw_data)
    
    # Price normalization
    df['discount_pct'] = ((df['original_price'] - df['discounted_price']) 
                         / df['original_price']) * 100
    
    # Outlier detection
    clf = LocalOutlierFactor(n_neighbors=20)
    outliers = clf.fit_predict(df[['discount_pct', 'original_price']])
    df = df[outliers == 1]
    
    # Geospatial validation
    valid_coords = df['location'].apply(
        lambda x: 40.477399 < x.lat < 40.917577 and 
                 -74.259090 < x.lon < -73.700272
    )
    
    return df[valid_coords].to_dict('records')