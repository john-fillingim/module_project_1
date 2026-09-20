import os
import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


df = pd.read_csv('/Users/prafulchunchu/Desktop/Duke/AIPI510/moduleProj1/module_project_1/data/raw/export.csv')

diseases_focus = ['Asthma', 'Cardiovascular Disease', 'Chronic Obstructive Pulmonary Disease', 'Diabetes']
data_sources = ['BRFSS', 'NVSS', 'CMS Part A Claims Data']

questions = {
    'Asthma': {
        'prevalence': {'source':'BRFSS', 'question': 'Current asthma among adults'},
        'mortality': {'source': 'NVSS', 'question':'Asthma mortality among all people, underlying cause'},
        'hospitalization': None
    },
    'Cardiovascular Disease': {
        'prevalence': {'source': 'BRFSS', 'question':'High blood pressure among adults'},
        'mortality': {'source': 'NVSS', 'question':'Diseases of the heart mortality among all people, underlying cause'},
        'hospitalization': {'source': 'CMS Part A Claims Data', 'question':'Hospitalization for heart failure as principal diagnosis, Medicare-beneficiaries aged 65 years and older'}
    },
    'Chronic Obstructive Pulmonary Disease': {
        'prevalence':{'source': 'BRFSS', 'question':'Chronic obstructive pulmonary disease among adults'},
        'mortality':{'source': 'NVSS', 'question':'Chronic obstructive pulmonary disease mortality among adults aged 45 years and older, underlying cause'},
        'hospitalization':{'source': 'CMS Part A Claims Data', 'question':'Hospitalization for chronic obstructive pulmonary disease as principal diagnosis, Medicare-beneficiaries aged 65 years and older'}
    },
    'Diabetes': {
        'prevalence':{'source': 'BRFSS', 'question':'Diabetes among adults'},
        'mortality':{'source': 'NVSS', 'question':'Diabetes mortality among all people, underlying or contributing cause'},
        'hospitalization': None
    }
}

cleaned_df = df