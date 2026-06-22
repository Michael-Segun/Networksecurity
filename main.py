

from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.entity.config_entity import DataIngestionConfig
from networksecurity.entity.config_entity import TrainingPipelineConfig

import sys

if __name__=='__main__':
    try:
        trainingpipelineconfig=TrainingPipelineConfig()
        DataIngestionConfig=DataIngestionConfig(trainingpipelineconfig)
        data_Ingestion=DataIngestion(DataIngestionConfig)
        logging.info("initiate the data ingestion")
        dataingestionartifact=data_Ingestion.initiate_data_ingestion()
        print(dataingestionartifact)
       
        
    
    except Exception as e:
        raise NetworkSecurityException(e,sys)
