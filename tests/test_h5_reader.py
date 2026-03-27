import pytest
import h5py
import numpy as np
import os
import tempfile
from src.core.h5_reader import H5Reader, H5File


@pytest.fixture
def temp_h5_file():
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
        temp_path = f.name
    
    with h5py.File(temp_path, 'w') as f:
        f.create_dataset('time', data=np.arange(0, 1000, 0.1))
        
        f.create_group('variables')
        f['variables'].create_dataset('V', data=np.sin(np.arange(0, 100, 0.1)))
        f['variables'].create_dataset('Cai', data=np.cos(np.arange(0, 100, 0.1)))
        f['variables'].create_dataset('l_1', data=np.ones(1000) * 2.0)
        
        f.create_group('currents')
        f['currents'].create_dataset('i_Na', data=np.random.randn(1000))
        f['currents'].create_dataset('i_rel', data=np.ones(1001) * 0.1)
        f['currents'].create_dataset('i_leak', data=np.ones(1001) * 0.01)
        f['currents'].create_dataset('i_up', data=np.ones(1001) * 0.05)
        f['currents'].create_dataset('i_xfer', data=np.ones(1001) * 0.02)
        f['currents'].create_dataset('i_CaL', data=np.ones(1001) * 0.03)
        f['currents'].create_dataset('i_b_Ca', data=np.ones(1001) * 0.001)
        f['currents'].create_dataset('i_p_Ca', data=np.ones(1001) * 0.002)
        f['currents'].create_dataset('i_NaCa', data=np.ones(1001) * 0.005)
        
        f.create_group('forces')
        f['forces'].create_dataset('F_XSE', data=np.random.randn(1000))
        
        f.create_group('parameters')
        f['parameters'].create_dataset('stim_period', data=np.array([1000.0]))
        f['parameters'].create_dataset('stim_start', data=np.array([10.0]))
        f['parameters'].create_dataset('V_jSR', data=np.array([0.01]))
        f['parameters'].create_dataset('V_c', data=np.array([0.02]))
        f['parameters'].create_dataset('V_nSR', data=np.array([0.005]))
        f['parameters'].create_dataset('V_ss', data=np.array([0.001]))
        f['parameters'].create_dataset('F', data=np.array([96485.0]))
        f['parameters'].create_dataset('Cm', data=np.array([1.0]))
    
    yield temp_path
    
    os.unlink(temp_path)


@pytest.fixture
def h5_reader():
    return H5Reader()


class TestH5Reader:
    def test_open_file(self, h5_reader, temp_h5_file):
        h5file = h5_reader.open_file(temp_h5_file)
        
        assert h5file is not None
        assert h5file.filename.endswith('.h5')
        assert h5file.time is not None
        assert len(h5file.time) == 10000
    
    def test_file_groups(self, h5_reader, temp_h5_file):
        h5file = h5_reader.open_file(temp_h5_file)
        
        assert 'variables' in h5file.groups
        assert 'currents' in h5file.groups
        assert 'forces' in h5file.groups
        assert 'parameters' in h5file.groups
    
    def test_file_datasets(self, h5_reader, temp_h5_file):
        h5file = h5_reader.open_file(temp_h5_file)
        
        assert 'V' in h5file.datasets['variables']
        assert 'Cai' in h5file.datasets['variables']
        assert 'i_Na' in h5file.datasets['currents']
        assert 'F_XSE' in h5file.datasets['forces']
    
    def test_parameters_loaded(self, h5_reader, temp_h5_file):
        h5file = h5_reader.open_file(temp_h5_file)
        
        assert h5file.cycle == 1000.0
        assert h5file.start_stim == 10.0
        assert h5file.Herz == 1.0
        assert h5file.count_cycle is not None
    
    def test_read_dataset(self, h5_reader, temp_h5_file):
        h5_reader.open_file(temp_h5_file)
        
        data = h5_reader.read_dataset('variables', 'V')
        
        assert data is not None
        assert len(data) == 1000
    
    def test_read_dataset_slice(self, h5_reader, temp_h5_file):
        h5_reader.open_file(temp_h5_file)
        
        data = h5_reader.read_dataset_slice('variables', 'V', 0, 100)
        
        assert data is not None
        assert len(data) == 100
    
    def test_read_nonexistent_dataset(self, h5_reader, temp_h5_file):
        h5_reader.open_file(temp_h5_file)
        
        data = h5_reader.read_dataset('variables', 'nonexistent')
        
        assert data is None
    
    def test_close_file(self, h5_reader, temp_h5_file):
        h5file = h5_reader.open_file(temp_h5_file)
        h5_reader.close_file(h5file)
        
        assert h5file not in h5_reader.files
    
    def test_multiple_files(self, h5_reader, temp_h5_file):
        h5file1 = h5_reader.open_file(temp_h5_file)
        h5file2 = h5_reader.open_file(temp_h5_file)
        
        assert len(h5_reader.files) == 2
        assert h5_reader.current_file == h5file2
    
    def test_close_all(self, h5_reader, temp_h5_file):
        h5_reader.open_file(temp_h5_file)
        h5_reader.open_file(temp_h5_file)
        
        h5_reader.close_all()
        
        assert len(h5_reader.files) == 0
        assert h5_reader.current_file is None
    
    def test_switch_current_file(self, h5_reader, temp_h5_file):
        h5file1 = h5_reader.open_file(temp_h5_file)
        h5file2 = h5_reader.open_file(temp_h5_file)
        
        h5_reader.current_file = h5file1
        assert h5_reader.current_file == h5file1


class TestH5File:
    def test_full_path(self, temp_h5_file):
        reader = H5Reader()
        h5file = reader.open_file(temp_h5_file)
        
        assert h5file.full_path == temp_h5_file
    
    def test_filename(self, temp_h5_file):
        reader = H5Reader()
        h5file = reader.open_file(temp_h5_file)
        
        assert '.h5' in h5file.filename


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
