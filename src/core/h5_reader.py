from dataclasses import dataclass
from typing import Dict, List, Optional
import h5py
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class H5File:
    path: str
    filename: str
    fid: h5py.File
    groups: List[str]
    datasets: Dict[str, List[str]]
    time: Optional[np.ndarray] = None
    cycle: Optional[float] = None
    start_stim: Optional[float] = None
    count_cycle: Optional[int] = None
    Herz: Optional[float] = None
    points_mod: Optional[int] = None
    
    @property
    def full_path(self) -> str:
        return self.path + self.filename


class H5Reader:
    def __init__(self):
        self.current_file: Optional[H5File] = None
        self.files: List[H5File] = []
    
    def open_file(self, filepath: str) -> H5File:
        filename = os.path.basename(filepath)
        path = os.path.dirname(filepath) + os.sep
        
        fid = h5py.File(filepath, 'r')
        
        groups = self._get_groups(fid)
        datasets = self._get_datasets(fid, groups)
        
        h5file = H5File(
            path=path,
            filename=filename,
            fid=fid,
            groups=groups,
            datasets=datasets
        )
        
        self._load_parameters(h5file)
        self.files.append(h5file)
        self.current_file = h5file
        
        return h5file
    
    def _get_groups(self, fid: h5py.File) -> List[str]:
        groups = []
        for key in fid.keys():
            if isinstance(fid[key], h5py.Group):
                groups.append(key)
        return groups
    
    def _get_datasets(self, fid: h5py.File, groups: List[str]) -> Dict[str, List[str]]:
        datasets = {}
        for group in groups:
            if group in fid:
                datasets[group] = list(fid[group].keys())
            else:
                datasets[group] = []
        return datasets
    
    def _load_parameters(self, h5file: H5File):
        try:
            h5file.time = h5file.fid['/time'][:]
        except KeyError:
            logger.warning("Could not load /time dataset")
            h5file.time = None
        
        try:
            val = h5file.fid['/parameters/stim_period'][()]
            h5file.cycle = float(val[0]) if val.ndim > 0 else float(val)
        except (KeyError, OSError):
            logger.warning("Could not load stim_period parameter")
            h5file.cycle = None
            
        try:
            val = h5file.fid['/parameters/stim_start'][()]
            h5file.start_stim = float(val[0]) if val.ndim > 0 else float(val)
        except (KeyError, OSError):
            logger.warning("Could not load stim_start parameter")
            h5file.start_stim = None
            
        if h5file.time is not None and h5file.cycle is not None:
            h5file.count_cycle = int(np.max(h5file.time) // h5file.cycle)
            h5file.Herz = 1000.0 / h5file.cycle
            h5file.points_mod = int(np.max(h5file.time) % h5file.cycle)
    
    def read_dataset(self, group: str, dataset: str) -> Optional[np.ndarray]:
        if self.current_file is None:
            return None
        try:
            path = f'/{group}/{dataset}'
            return self.current_file.fid[path][:]
        except (KeyError, OSError) as e:
            logger.warning(f"Could not read dataset {group}/{dataset}: {e}")
            return None
    
    def read_dataset_slice(self, group: str, dataset: str, start: int, count: int) -> Optional[np.ndarray]:
        if self.current_file is None:
            return None
        try:
            path = f'/{group}/{dataset}'
            return self.current_file.fid[path][start:start+count]
        except (KeyError, OSError) as e:
            logger.warning(f"Could not read slice from {group}/{dataset}: {e}")
            return None
    
    def close_file(self, h5file: H5File):
        h5file.fid.close()
        if h5file in self.files:
            self.files.remove(h5file)
        if self.current_file == h5file:
            self.current_file = self.files[0] if self.files else None
    
    def close_all(self):
        for f in self.files:
            try:
                f.fid.close()
            except OSError as e:
                logger.warning(f"Could not close file {f.filename}: {e}")
        self.files.clear()
        self.current_file = None