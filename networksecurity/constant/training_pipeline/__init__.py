import os
import sys
import numpy as np
import pandas as pd


"""
This file holds nothing but plain values. No logic, no classes, no computation. Just labeled constants:
Think of it as your project's settings sheet. If tomorrow you want to rename "Artifacts" to "Outputs", 
you change it once, here, and every part of the pipeline that depends on it updates automatically
"""




"""
defining common constant variable for training pipeline

"""

TARGET_COLUMN ="Result"
PIPELINE_NAME: str = "NetworkSecurity"
ARTIFACT_DIR: str = "Artifacts"
FILE_NAME: str = "phisingData.csv"

TRAIN_FILE_NAME: str = "train.csv"
TEST_FILE_NAME: str = "test.csv"


"""
    Data Ingestion related constant start with DATA_INGESTION VAR NAME
"""
    
DATA_INGESTION_COLLECTION_NAME: str = "NetworkData"
DATA_INGESTION_DATABASE_NAME: str = "SegunMichael"
DATA_INGESTION_DIR_NAME: str = "data ingestion"
DATA_INGESTION_FEATURE_STORE_DIR: str = "feature_store"
DATA_INGESTION_INGESTED_DIR: str = "ingested"
DATA_INGESTED_TRAIN_TEST_SPLIT_RATION: float = 0.2