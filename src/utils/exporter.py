import pandas as pd
from typing import Dict, Any, Optional
import numpy as np
import os
from datetime import datetime


class ExcelExporter:
    @staticmethod
    def save_to_excel(data: Dict[str, Any], filename: str, sheet_name: str = 'Data'):
        df = pd.DataFrame(data)
        df.to_excel(filename, sheet_name=sheet_name, index=False)
    
    @staticmethod
    def save_all_cycles(time: np.ndarray, data_dict: Dict[str, np.ndarray], 
                        filename: str, file_label: str):
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            time_df = pd.DataFrame({'time (ms)': time})
            time_df.to_excel(writer, sheet_name='Data', index=False, startcol=0)
            
            col_idx = 1
            for dataset_name, data in data_dict.items():
                col_letter = chr(ord('A') + col_idx)
                df = pd.DataFrame({dataset_name: data})
                df.to_excel(writer, sheet_name='Data', index=False, startcol=col_idx)
                col_idx += 1
    
    @staticmethod
    def save_cycle_data(time: np.ndarray, data_dict: Dict[str, np.ndarray],
                        characteristics: Dict[str, Any],
                        filename: str, file_label: str, cycle_type: str = 'last'):
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            time_df = pd.DataFrame({'time (ms)': time})
            time_df.to_excel(writer, sheet_name='Data_for_figs', index=False, startcol=0)
            
            col_idx = 1
            for dataset_name, data in data_dict.items():
                col_letter = chr(ord('B') + col_idx)
                df = pd.DataFrame({dataset_name: data})
                df.to_excel(writer, sheet_name='Data_for_figs', index=False, startcol=col_idx)
                col_idx += 1
            
            row = 1
            char_df = pd.DataFrame({
                'Characteristics': [],
                'Value': []
            })
            
            if 'Frequency (Hz)' in characteristics:
                char_df = pd.concat([char_df, pd.DataFrame({
                    'Characteristics': ['Frequency (Hz)', ''],
                    'Value': [characteristics.get('Frequency (Hz)', ''), '']
                })])
            
            for key, value in characteristics.items():
                if key != 'Frequency (Hz)':
                    char_df = pd.concat([char_df, pd.DataFrame({
                        'Characteristics': [key],
                        'Value': [value]
                    })])
            
            char_df.to_excel(writer, sheet_name='Characteristics_for_figs', index=False)
    
    @staticmethod
    def save_parameters(params: Dict[str, Any], filename: str):
        param_df = pd.DataFrame({
            'Parameter': list(params.keys()),
            'Value': list(params.values())
        })
        param_df.to_excel(filename, sheet_name='Parameters', index=False)
    
    @staticmethod
    def save_last_vars(first_values: Dict[str, float], last_values: Dict[str, float],
                       cycle: int, count_cycle: int, Herz: float, filename: str):
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            last_df = pd.DataFrame({
                'Variable': list(last_values.keys()),
                'Last Value': list(last_values.values())
            })
            last_df.to_excel(writer, sheet_name='Last_vars_values', index=False)
            
            first_df = pd.DataFrame({
                'Variable': list(first_values.keys()),
                'First Value': list(first_values.values())
            })
            first_df.to_excel(writer, sheet_name='First_vars_values', index=False)
            
            info_df = pd.DataFrame({
                'Parameter': ['Cycle length (ms)', 'Number of cycles', 'Frequency (Hz)'],
                'Value': [cycle, count_cycle, Herz]
            })
            info_df.to_excel(writer, sheet_name='Last_vars_values', index=False, startrow=5)
    
    @staticmethod
    def save_dependencies(dep_data: pd.DataFrame, filename: str):
        dep_data.to_excel(filename, sheet_name='Dependencies', index=False)
    
    @staticmethod
    def save_integrals(int_data: pd.DataFrame, filename: str):
        int_data.to_excel(filename, sheet_name='Integrals', index=False)