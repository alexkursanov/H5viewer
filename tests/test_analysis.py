import pytest
import numpy as np
from src.utils.analysis import DataAnalyzer


class TestDataAnalyzer:
    @pytest.fixture
    def sample_voltage_data(self):
        time = np.linspace(0, 100, 1000)
        v = np.zeros(1000)
        v[100:300] = np.linspace(-80, 40, 200)
        v[300:] = np.linspace(40, -80, 700)
        return time, v
    
    @pytest.fixture
    def sample_force_data(self):
        f = np.zeros(1000)
        f[100:400] = np.linspace(0, 1, 300)
        f[400:] = np.linspace(1, 0, 600)
        return f
    
    @pytest.fixture
    def sample_calcium_data(self):
        cai = np.zeros(1000)
        cai[100:350] = np.linspace(0.1, 1.0, 250)
        cai[350:] = np.linspace(1.0, 0.1, 650)
        return cai

    def test_calculate_characteristics(self, sample_voltage_data):
        time, v = sample_voltage_data
        
        result = DataAnalyzer.calculate_characteristics(
            v, time, cycle=1000, start_stim=100
        )
        
        assert 'V_max' in result
        assert 'V_min' in result
        assert 'V_ampl' in result
        assert 'APD20' in result
        assert 'APD50' in result
        assert 'APD90' in result
    
    def test_calculate_force_characteristics(self, sample_force_data):
        result = DataAnalyzer.calculate_force_characteristics(
            sample_force_data, start_stim=100
        )
        
        assert 'FXSE_max' in result
        assert 'FXSE_min' in result
        assert 'FXSE_ampl' in result
        assert 'tFXSE_max' in result
        assert 'FXSE_D50' in result
        assert 'DF_max' in result
        assert 'DF_min' in result
    
    def test_calculate_calcium_characteristics(self, sample_calcium_data):
        result = DataAnalyzer.calculate_calcium_characteristics(
            sample_calcium_data, start_stim=100
        )
        
        assert 'Cai_max' in result
        assert 'Cai_min' in result
        assert 'Cai_ampl' in result
        assert 'tCai_max' in result
        assert 'Cai_D10' in result
        assert 'Cai_D50' in result
        assert 'Cai_D90' in result
    
    def test_calculate_length_characteristics(self):
        l = np.ones(1000) * 2.0
        l[100:300] = np.linspace(2.0, 1.5, 200)
        l[300:] = np.linspace(1.5, 2.0, 700)
        
        result = DataAnalyzer.calculate_length_characteristics(l, start_stim=100)
        
        assert 'l1_diast' in result
        assert 'l1_syst' in result
        assert 'l1_diff' in result
        assert 'l1_frac' in result
    
    def test_empty_data(self):
        result = DataAnalyzer.calculate_characteristics(
            np.array([]), np.array([]), cycle=100
        )
        
        assert result == {}
    
    def test_get_last_cycle_data(self):
        time = np.arange(0, 3000, 1)
        data = np.sin(time / 100)
        
        t_shift, data_cycle = DataAnalyzer.get_last_cycle_data(
            time, data, cycle=1000, points_mod=0
        )
        
        assert t_shift is not None
        assert data_cycle is not None
        assert len(t_shift) <= 1000
        assert len(t_shift) == len(data_cycle)


class TestDataAnalyzerIntegrals:
    def test_calculate_calcium_integrals(self):
        data_dict = {
            'i_rel': np.ones(1001) * 0.1,
            'i_leak': np.ones(1001) * 0.01,
            'i_up': np.ones(1001) * 0.05,
            'i_xfer': np.ones(1001) * 0.02,
        }
        
        params = {
            'V_jSR': 0.01,
            'V_c': 0.02,
            'V_nSR': 0.005,
            'V_ss': 0.001,
            'F': 96485,
            'Cm': 1.0
        }
        
        result = DataAnalyzer.calculate_calcium_integrals(
            data_dict, params, cycle=1000
        )
        
        assert 'Int_i_relSR' in result
        assert 'Int_i_leak' in result
        assert 'Int_i_up' in result
        assert 'Int_i_xfercyt' in result
    
    def test_calculate_calcium_integrals_empty(self):
        result = DataAnalyzer.calculate_calcium_integrals({}, {}, 1000)
        
        assert result == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])