import pandas as pd
import os

try:
    df = pd.read_csv('backend/dataset.csv')
    
    # Normalize columns
    df.rename(columns={
        'animal_type': 'animal',
        'symptom_1': 'Symptom1',
        'symptom_2': 'Symptom2',
        'symptom_3': 'Symptom3',
        'medicine': 'Remedy1',
        'care_1': 'Remedy2',
        'care_2': 'Remedy3'
    }, inplace=True)
    
    print("--- DISEASES ---")
    print(df['disease'].unique())
    
    print("\n--- MEDICINES ---")
    print(df['Remedy1'].unique())
    
    print("\n--- CARE ---")
    care_values = set(df['Remedy2'].unique()) | set(df['Remedy3'].unique())
    print(care_values)
    
except Exception as e:
    print(e)
