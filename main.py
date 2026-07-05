

from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.components.data_validation import DataValidation
from networksecurity.components.data_transformation import DataTransformation
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.entity.config_entity import DataIngestionConfig, DataValidationConfig, DataTransformationConfig
from networksecurity.entity.config_entity import TrainingPipelineConfig

import sys

if __name__=='__main__':
    try:
        trainingpipelineconfig=TrainingPipelineConfig()
        Data_Ingestion_config=DataIngestionConfig(trainingpipelineconfig)
        data_Ingestion=DataIngestion(Data_Ingestion_config)
        logging.info("initiate the data ingestion")
        dataingestionartifact=data_Ingestion.initiate_data_ingestion()
        logging.info("Data Initiation completed")
        print(dataingestionartifact)
        data_validation_config=DataValidationConfig(trainingpipelineconfig)
        data_validaion=DataValidation(dataingestionartifact,data_validation_config)
        logging.info("Initiate the data Validation")
        data_validation_artifact=data_validaion.initiate_data_validation()
        logging.info("data validation completed")
        print(data_validation_artifact)
        data_transformation_config=DataTransformationConfig(trainingpipelineconfig)
        logging.info("Data Transformation Started")
        data_transformation=DataTransformation(data_validation_artifact,data_transformation_config)
        data_transformation_artifact=data_transformation.initiate_data_transformation()
        print(data_transformation_artifact)
        logging.info("Data Transformation completed")
        
    
    except Exception as e:
        raise NetworkSecurityException(e,sys)
