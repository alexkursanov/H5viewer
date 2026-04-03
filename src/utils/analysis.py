"""
Data analysis utilities for H5 Reader.

Provides functions for analyzing cardiomyocte simulation data.
"""
import numpy as np
from typing import Dict, Any, Optional


def _calculate_apd(data: np.ndarray, start_stim: int, levels: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate APD at different levels.
    
    Args:
        data: Signal data
        start_stim: Stimulation start index
        levels: Dict of level_name -> fraction (e.g., {'V20': 0.8, 'V50': 0.5})
    
    Returns:
        Dict with APD values
    """
    results = {}
    min_val = data[start_stim] if start_stim < len(data) else data[0]
    max_val = np.max(data)
    ampl = max_val - min_val
    
    tVmax = np.argmax(data) - start_stim
    
    for name, fraction in levels.items():
        threshold = min_val + fraction * ampl
        indices = np.where(data > threshold)[0]
        duration = indices[-1] - (tVmax + start_stim) if len(indices) > 0 else 0
        results[name] = duration
    
    return results


class DataAnalyzer:
    """
    Analyzer for cardiomyocyte simulation data.
    
    Provides methods to calculate various characteristics like APD, force, calcium, etc.
    """
    
    @staticmethod
    def calculate_characteristics(data: np.ndarray, time: np.ndarray, 
                                  cycle: int, start_stim: int = 10) -> Dict[str, Any]:
        """
        Calculate voltage characteristics including APD.
        
        Args:
            data: Voltage data array
            time: Time array
            cycle: Cycle length
            start_stim: Stimulation start index
        
        Returns:
            Dict with V_max, V_min, APD values, etc.
        """
        results = {}
        
        if data is None or len(data) == 0:
            return results
        
        ampl = np.max(data) - np.min(data)
        
        if np.max(data) == np.min(data):
            return {'error': 'Constant data'}
        
        apd_results = _calculate_apd(data, start_stim, {
            'APD20': 0.8, 'APD50': 0.5, 'APD90': 0.1
        })
        
        results['V_max'] = np.max(data)
        results['V_min'] = np.min(data)
        results['V_ampl'] = ampl
        results['tV_max'] = np.argmax(data) - start_stim
        results.update(apd_results)
        
        return results
    
    @staticmethod
    def calculate_force_characteristics(data: np.ndarray, 
                                        start_stim: int = 10) -> Dict[str, Any]:
        """
        Calculate force characteristics.
        
        Args:
            data: Force data array
            start_stim: Stimulation start index
        
        Returns:
            Dict with FXSE_max, FXSE_D values, etc.
        """
        results = {}
        
        if data is None or len(data) == 0:
            return results
        
        min_val = data[start_stim] if start_stim < len(data) else data[0]
        ampl = np.max(data) - min_val
        
        apd_results = _calculate_apd(data, start_stim, {
            'FXSE_D50': 0.5, 'FXSE_D70': 0.3, 'FXSE_D90': 0.1
        })
        
        tFmax = np.argmax(data) - start_stim
        
        DFup = np.diff(data[:tFmax+1]) if tFmax > 0 else []
        DFdown = np.diff(data[tFmax:]) if tFmax < len(data) - 1 else []
        
        results['FXSE_max'] = np.max(data)
        results['FXSE_min'] = min_val
        results['FXSE_ampl'] = ampl
        results['tFXSE_max'] = tFmax
        results.update(apd_results)
        results['DF_max'] = np.max(DFup) if len(DFup) > 0 else 0
        results['DF_min'] = np.min(DFdown) if len(DFdown) > 0 else 0
        results['DF_max_norm'] = np.max(DFup) / ampl if ampl > 0 else 0
        results['DF_min_norm'] = np.min(DFdown) / ampl if ampl > 0 else 0
        
        return results
    
    @staticmethod
    def calculate_calcium_characteristics(data: np.ndarray, 
                                          start_stim: int = 10) -> Dict[str, Any]:
        """
        Calculate calcium characteristics.
        
        Args:
            data: Calcium data array
            start_stim: Stimulation start index
        
        Returns:
            Dict with Cai_max, Cai_D values, etc.
        """
        results = {}
        
        if data is None or len(data) == 0:
            return results
        
        min_val = data[start_stim] if start_stim < len(data) else data[0]
        ampl = np.max(data) - min_val
        
        apd_results = _calculate_apd(data, start_stim, {
            'Cai_D10': 0.9, 'Cai_D50': 0.5, 'Cai_D70': 0.3, 'Cai_D90': 0.1
        })
        
        results['Cai_max'] = np.max(data) * 1000
        results['Cai_min'] = min_val * 1000
        results['Cai_ampl'] = ampl * 1000
        results['tCai_max'] = np.argmax(data) - start_stim
        results.update(apd_results)
        
        return results
    
    @staticmethod
    def calculate_length_characteristics(data: np.ndarray, 
                                          start_stim: int = 10) -> Dict[str, Any]:
        """
        Calculate length characteristics.
        
        Args:
            data: Length data array
            start_stim: Stimulation start index
        
        Returns:
            Dict with l1_diast, l1_syst, etc.
        """
        results = {}
        
        if data is None or len(data) == 0:
            return results
        
        l1_diast = np.max(data)
        l1_syst = np.min(data)
        l1_diff = l1_diast - l1_syst
        l1_frac = 100 - (l1_diff + 1.67) / (l1_diast + 1.67) * 100
        
        results['Lmuscle'] = data[start_stim] if start_stim < len(data) else data[0]
        results['l1_diast'] = l1_diast
        results['l1_syst'] = l1_syst
        results['l1_diff'] = l1_diff
        results['l1_frac'] = l1_frac
        
        return results
    
    @staticmethod
    def calculate_calcium_integrals(data_dict: Dict[str, np.ndarray], 
                                    params: Dict[str, float],
                                    cycle: int) -> Dict[str, float]:
        """
        Calculate calcium handling integrals.
        
        Args:
            data_dict: Dict of current names to data arrays
            params: Dict of parameters (V_jSR, V_c, etc.)
            cycle: Cycle length
        
        Returns:
            Dict with integral values
        """
        results = {}
        
        VjSR = params.get('V_jSR', 1)
        Vc = params.get('V_c', 1)
        VnSR = params.get('V_nSR', 1)
        Vss = params.get('V_ss', 1)
        FF = params.get('F', 1)
        Cm = params.get('Cm', 1)
        
        ht = 1.0
        
        def integrate(current, coeff):
            return np.sum(current[:cycle+1]) * ht * coeff
        
        if 'i_rel' in data_dict:
            irel = data_dict['i_rel']
            results['Int_i_relSR'] = integrate(irel, 1)
            results['Int_i_relcyt'] = integrate(irel, VjSR / Vc)
            results['Int_i_relSS'] = integrate(irel, VjSR / Vss)
        
        if 'i_leak' in data_dict:
            ileak = data_dict['i_leak']
            results['Int_i_leak'] = integrate(ileak, 1)
        
        if 'i_up' in data_dict:
            iup = data_dict['i_up']
            results['Int_i_up'] = integrate(iup, 1)
        
        if 'i_xfer' in data_dict:
            ixfer = data_dict['i_xfer']
            results['Int_i_xfercyt'] = integrate(ixfer, 1)
            results['Int_i_xferSS'] = integrate(ixfer, Vc / Vss)
        
        if 'i_b_Ca' in data_dict:
            ibCa = data_dict['i_b_Ca']
            results['Int_i_bCa'] = integrate(ibCa, Cm / (2 * Vc * FF))
        
        if 'i_p_Ca' in data_dict:
            ipCa = data_dict['i_p_Ca']
            results['Int_i_pCa'] = integrate(ipCa, Cm / (2 * Vc * FF))
        
        return results
    
    @staticmethod
    def get_last_cycle_data(time: np.ndarray, data: np.ndarray, 
                            cycle: int, points_mod: int) -> tuple:
        """
        Extract data for the last cycle.
        
        Args:
            time: Full time array
            data: Full data array
            cycle: Cycle length
            points_mod: Points modulo
        
        Returns:
            Tuple of (shifted_time, cycle_data)
        """
        if time is None or data is None:
            return None, None
            
        t_start = int(np.max(time) + 1 - cycle - points_mod)
        t_end = int(np.max(time) + 1 - points_mod)
        
        t = time[t_start:t_end+1]
        data_cycle = data[t_start:t_end+1]
        t_shift = t - t[0]
        
        return t_shift, data_cycle