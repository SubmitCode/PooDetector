# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/05_preview_folder.ipynb (unless otherwise specified).

__all__ = ['convert_path_timestamp', 'create_datehour_folders']

# Cell
import os
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd

# Cell
def convert_path_timestamp(path:[str,Path]):
    """converts a filename to timestamp"""
    path = Path(path)
    if path.is_file() is False:
        return None

    filename = path.stem
    return datetime.strptime(filename[:14], '%Y%m%d%H%M%S')

# Cell
def create_datehour_folders(path:[str, Path], df:pd.DataFrame):
    """create a folder for every datehour combination in the dataframe"""
    assert 'datehour' in df.columns
    path = Path(path)
    for datehour in df.datehour.unique():
        print(f"create folder {datehour}")
        (path / str(datehour)).mkdir(exist_ok=True)