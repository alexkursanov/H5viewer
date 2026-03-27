import numpy as np
from typing import Dict, Any, Optional


class DataAnalyzer:
    @staticmethod
    def calculate_characteristics(data: np.ndarray, time: np.ndarray, 
                                  cycle: int, start_stim: int = 10) -> Dict[str, Any]:
        results = {}
        
        if data is None or len(data) == 0:
            return results
        
        ampl = np.max(data) - np.min(data)
        
        if np.max(data) == np.min(data):
            return {'error': 'Constant data'}
        
        tVmax = np.argmax(data) - start_stim
        
        V20 = 0.8 * ampl + np.min(data)
        V50 = 0.5 * ampl + np.min(data)
        V90 = 0.1 * ampl + np.min(data)
        
        Vup = np.where(data > V20)[0]
        APD20 = Vup[-1] - (tVmax + start_stim) if len(Vup) > 0 else 0
        
        Vup = np.where(data > V50)[0]
        APD50 = Vup[-1] - (tVmax + start_stim) if len(Vup) > 0 else 0
        
        Vup = np.where(data > V90)[0]
        APD90 = Vup[-1] - (tVmax + start_stim) if len(Vup) > 0 else 0
        
        results['V_max'] = np.max(data)
        results['V_min'] = np.min(data)
        results['V_ampl'] = ampl
        results['tV_max'] = tVmax
        results['APD20'] = APD20
        results['APD50'] = APD50
        results['APD90'] = APD90
        
        return results
    
    @staticmethod
    def calculate_force_characteristics(data: np.ndarray, 
                                        start_stim: int = 10) -> Dict[str, Any]:
        results = {}
        
        if data is None or len(data) == 0:
            return results
        
        min_val = data[start_stim] if start_stim < len(data) else data[0]
        ampl = np.max(data) - min_val
        
        tFmax = np.argmax(data) - start_stim
        
        F50 = 0.5 * ampl + min_val
        F70 = 0.3 * ampl + min_val
        F90 = 0.1 * ampl + min_val
        
        Fup = np.where(data > F50)[0]
        FXSE_D50 = Fup[-1] - (tFmax + start_stim) if len(Fup) > 0 else 0
        
        Fup = np.where(data > F70)[0]
        FXSE_D70 = Fup[-1] - (tFmax + start_stim) if len(Fup) > 0 else 0
        
        Fup = np.where(data > F90)[0]
        FXSE_D90 = Fup[-1] - (tFmax + start_stim) if len(Fup) > 0 else 0
        
        DFup = np.diff(data[:tFmax+1]) if tFmax > 0 else []
        DFdown = np.diff(data[tFmax:]) if tFmax < len(data) - 1 else []
        
        results['FXSE_max'] = np.max(data)
        results['FXSE_min'] = min_val
        results['FXSE_ampl'] = ampl
        results['tFXSE_max'] = tFmax
        results['FXSE_D50'] = FXSE_D50
        results['FXSE_D70'] = FXSE_D70
        results['FXSE_D90'] = FXSE_D90
        results['DF_max'] = np.max(DFup) if len(DFup) > 0 else 0
        results['DF_min'] = np.min(DFdown) if len(DFdown) > 0 else 0
        results['DF_max_norm'] = np.max(DFup) / ampl if ampl > 0 else 0
        results['DF_min_norm'] = np.min(DFdown) / ampl if ampl > 0 else 0
        
        return results
    
    @staticmethod
    def calculate_calcium_characteristics(data: np.ndarray, 
                                          start_stim: int = 10) -> Dict[str, Any]:
        results = {}
        
        if data is None or len(data) == 0:
            return results
        
        min_val = data[start_stim] if start_stim < len(data) else data[0]
        ampl = np.max(data) - min_val
        
        tCamax = np.argmax(data) - start_stim
        
        Ca10 = 0.9 * ampl + min_val
        Ca50 = 0.5 * ampl + min_val
        Ca70 = 0.3 * ampl + min_val
        Ca90 = 0.1 * ampl + min_val
        
        Caup = np.where(data > Ca10)[0]
        CaD10 = Caup[-1] - (tCamax + start_stim) if len(Caup) > 0 else 0
        
        Caup = np.where(data > Ca50)[0]
        CaD50 = Caup[-1] - (tCamax + start_stim) if len(Caup) > 0 else 0
        
        Caup = np.where(data > Ca70)[0]
        CaD70 = Caup[-1] - (tCamax + start_stim) if len(Caup) > 0 else 0
        
        Caup = np.where(data > Ca90)[0]
        CaD90 = Caup[-1] - (tCamax + start_stim) if len(Caup) > 0 else 0
        
        results['Cai_max'] = np.max(data) * 1000
        results['Cai_min'] = min_val * 1000
        results['Cai_ampl'] = ampl * 1000
        results['tCai_max'] = tCamax
        results['Cai_D10'] = CaD10
        results['Cai_D50'] = CaD50
        results['Cai_D70'] = CaD70
        results['Cai_D90'] = CaD90
        
        return results
    
    @staticmethod
    def calculate_length_characteristics(data: np.ndarray, 
                                          start_stim: int = 10) -> Dict[str, Any]:
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
        if time is None or data is None:
            return None, None
            
        t_start = int(np.max(time) + 1 - cycle - points_mod)
        t_end = int(np.max(time) + 1 - points_mod)
        
        t = time[t_start:t_end+1]
        data_cycle = data[t_start:t_end+1]
        t_shift = t - t[0]
        
        return t_shift, data_cycle