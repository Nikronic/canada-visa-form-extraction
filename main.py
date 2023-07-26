"""
Only run this code for generating [dataset_name].pkl file, every time we want to create a new version
of our dataset, then after this step, we use DVC to version it.
In main.py, we just rerun this step but integrated into MLFlow to track which version we are
USING (than generating).

In simple terms, if you added new samples, changed columns or anything that should be considered
permanent at the time, you should run this script, then version it with DVC and for doing
data analysis or machine learning for prediction, only pull from DVC remote storage of 
this version (or any version you want).
"""

# core
import pandas as pd
# ours: data
from cvfe.data.constant import DocTypes
from cvfe.data import functional
from cvfe.data.preprocessor import MakeContentCopyProtectedMachineReadable
from cvfe.data.preprocessor import CanadaDataframePreprocessor
from cvfe.data.preprocessor import FileTransformCompose
from cvfe.data.preprocessor import CopyFile
# helpers
from pathlib import Path
import logging
import shutil
import sys
import os


if __name__ == '__main__':
    # globals
    VERBOSE = logging.DEBUG

    # configure logging
    logger = logging.getLogger(__name__)
    logger.setLevel(VERBOSE)

    # main path
    # TODO: get from user 
    SRC_DIR = 'sample/encrypted/'  # path to the source encrypted pdf
    # TODO: get from user 
    DST_DIR = 'sample/decrypted/'  # path to the output decrypted pdf

    # main code
    logger.info('↓↓↓ Starting data extraction ↓↓↓')
    # Canada protected PDF to make machine readable and skip other files
    compose = {
        CopyFile(mode='cf'): '.csv',
        CopyFile(mode='cf'): '.txt',
        MakeContentCopyProtectedMachineReadable(): '.pdf'
    }
    file_transform_compose = FileTransformCompose(transforms=compose)
    functional.process_directory(
        src_dir=SRC_DIR,
        dst_dir=DST_DIR,
        compose=file_transform_compose,
        file_pattern='*')
    logger.info('↑↑↑ Finished data extraction ↑↑↑')

    logger.info('↓↓↓ Starting data loading ↓↓↓')
    # convert PDFs to pandas dataframes
    SRC_DIR = DST_DIR[:-1]
    dataframe = pd.DataFrame()
    for dirpath, dirnames, all_filenames in os.walk(SRC_DIR):

        # filter all_filenames
        filenames = all_filenames
        if filenames:
            files = [os.path.join(dirpath, fname) for fname in filenames]
            # applicant form
            logger.info('↓↓↓ Starting to process 5257E ↓↓↓')
            in_fname = [f for f in files if '5257' in f][0]
            df_preprocessor = CanadaDataframePreprocessor()
            if len(in_fname) != 0:
                dataframe_applicant = df_preprocessor.file_specific_basic_transform(
                    path=in_fname,
                    type=DocTypes.canada_5257e)
            logger.info('↑↑↑ Finished processing 5257E ↑↑↑')
            # applicant family info
            logger.info('↓↓↓ Starting to process 5645E ↓↓↓')
            in_fname = [f for f in files if '5645' in f][0]
            if len(in_fname) != 0:
                dataframe_family = df_preprocessor.file_specific_basic_transform(
                    path=in_fname,
                    type=DocTypes.canada_5645e)
            logger.info('↑↑↑ Finished processing 5645E ↑↑↑')
            # manually added labels
            logger.info('↓↓↓ Starting to process the label ↓↓↓')
            in_fname = [f for f in files if 'label' in f][0]
            if len(in_fname) != 0:
                dataframe_label = df_preprocessor.file_specific_basic_transform(
                    path=in_fname,
                    type=DocTypes.canada_label)
            logger.info('↑↑↑ Finished processing the label ↑↑↑')

            # final dataframe: concatenate common forms and label column wise
            dataframe = pd.concat(
                objs=[
                    dataframe_applicant,
                    dataframe_family,
                    dataframe_label],
                axis=1, verify_integrity=True)
        
        # logging
        logger.info(f'Processed the data point')

    data = dataframe
    logger.info('↑↑↑ Finished data loading ↑↑↑')
