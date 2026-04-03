from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QMenuBar, QMenu, QFileDialog, QMessageBox, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QSplitter, QFrame,
    QStatusBar, QComboBox, QSlider, QDialog, QInputDialog, QLineEdit,
    QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
import numpy as np
import logging
import os
import tempfile

from src.core.h5_reader import H5Reader, H5File
from src.utils.ssh_client import SSHConnection, SSHDialog
from src.ui.tabs import AllCyclesTab, LastCycleTab, DependenciesTab, IntegralsTab


VERSION = '1.0'
AUTHOR = 'Nathalie A. Balakina-Vikulova'

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.h5_reader: H5Reader = H5Reader()
        self.current_file: Optional[H5File] = None
        self.files: List[H5File] = []
        
        self.ssh_connection = SSHConnection()
        self.temp_dir = tempfile.mkdtemp()
        self.download_dir: str = ''
        
        self.all_cycles_tab: Optional[AllCyclesTab] = None
        self.last_cycle_tab: Optional[LastCycleTab] = None
        self.dependencies_tab: Optional[DependenciesTab] = None
        self.integrals_tab: Optional[IntegralsTab] = None
        
        self.setup_ui()

    def setup_ui(self) -> None:
        self.setWindowTitle(f'H5 Reader v{VERSION}')
        self.setGeometry(100, 100, 1200, 800)
        
        self._create_menu()
        self._create_central_widget()
        self._create_status_bar()

    def _create_menu(self) -> None:
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open H5 File', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_menu = QMenu('Save Data to XLS', self)
        file_menu.addMenu(save_menu)
        
        save_all_cycles = QAction('Save All Cycles', self)
        save_all_cycles.triggered.connect(self.save_all_cycles)
        save_menu.addAction(save_all_cycles)
        
        save_first_cycle = QAction('Save First Cycle', self)
        save_first_cycle.triggered.connect(self.save_first_cycle)
        save_menu.addAction(save_first_cycle)
        
        save_last_cycle = QAction('Save Last Cycle', self)
        save_last_cycle.triggered.connect(self.save_last_cycle)
        save_menu.addAction(save_last_cycle)
        
        save_params = QAction('Save Parameters', self)
        save_params.triggered.connect(self.save_parameters)
        save_menu.addAction(save_params)
        
        save_vars = QAction('Save Vars (1st and Last values)', self)
        save_vars.triggered.connect(self.save_vars)
        save_menu.addAction(save_vars)
        
        save_charts = QAction('Save Charts to XLS', self)
        save_charts.triggered.connect(self.save_charts)
        save_menu.addAction(save_charts)
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        ssh_menu = menubar.addMenu('SSH')
        
        connect_action = QAction('Connect to Server', self)
        connect_action.triggered.connect(self.ssh_connect)
        ssh_menu.addAction(connect_action)
        
        disconnect_action = QAction('Disconnect', self)
        disconnect_action.triggered.connect(self.ssh_disconnect)
        ssh_menu.addAction(disconnect_action)
        
        ssh_menu.addSeparator()
        
        browse_action = QAction('Browse Remote Files', self)
        browse_action.triggered.connect(self.ssh_browse)
        ssh_menu.addAction(browse_action)
        
        help_menu = menubar.addMenu('Help')
        
        docs_action = QAction('Documentation', self)
        docs_action.setShortcut('F1')
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_central_widget(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        
        layout.addWidget(splitter)

    def _create_left_panel(self) -> QWidget:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setMaximumWidth(300)
        
        layout = QVBoxLayout(frame)
        
        layout.addWidget(QLabel('Files:'))
        
        self.files_list = QListWidget()
        self.files_list.itemClicked.connect(self.on_file_selected)
        layout.addWidget(self.files_list)
        
        self.delete_file_btn = QPushButton('Delete')
        self.delete_file_btn.setEnabled(False)
        self.delete_file_btn.clicked.connect(self.delete_file)
        layout.addWidget(self.delete_file_btn)
        
        layout.addWidget(QLabel('H5 Structure:'))
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(['Name', 'Value'])
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        layout.addWidget(self.tree_widget)
        
        self.info_label = QLabel()
        layout.addWidget(self.info_label)
        
        return frame
    
    def _create_right_panel(self) -> QWidget:
        self.tab_widget = QTabWidget()
        
        self.all_cycles_tab = AllCyclesTab(self, self.h5_reader, lambda: self.current_file)
        self.last_cycle_tab = LastCycleTab(self, self.h5_reader, lambda: self.current_file)
        self.dependencies_tab = DependenciesTab(self)
        self.integrals_tab = IntegralsTab(self)
        
        self._connect_tab_signals()
        
        self.tab_widget.addTab(self.all_cycles_tab.get_widget(), 'All Cycles')
        self.tab_widget.addTab(self.last_cycle_tab.get_widget(), 'Last Cycle')
        self.tab_widget.addTab(self.dependencies_tab.get_widget(), 'Dependencies')
        self.tab_widget.addTab(self.integrals_tab.get_widget(), 'Integrals')
        
        return self.tab_widget
    
    def _connect_tab_signals(self) -> None:
        self.all_cycles_tab.single_mode_btn.clicked.connect(self.set_single_mode)
        self.all_cycles_tab.multiple_mode_btn.clicked.connect(self.set_multiple_mode)
        self.all_cycles_tab.show_stimuli_check.clicked.connect(self.toggle_stimuli)
        self.all_cycles_tab.clear_chart_btn.clicked.connect(self.all_cycles_tab.clear_chart)
        self.all_cycles_tab.up_slider.valueChanged.connect(self.all_cycles_tab.update_x_range)
        self.all_cycles_tab.down_slider.valueChanged.connect(self.all_cycles_tab.update_x_range)
        
        self.last_cycle_tab.plot_btn.clicked.connect(self.last_cycle_tab.plot)
        self.last_cycle_tab.prev_page_btn.clicked.connect(self.last_cycle_tab.prev_page)
        self.last_cycle_tab.next_page_btn.clicked.connect(self.last_cycle_tab.next_page)
        self.last_cycle_tab.total_clear_btn.clicked.connect(self.last_cycle_tab.clear)
        self.last_cycle_tab.remove_selected_btn.clicked.connect(self.last_cycle_tab.remove_selected)
        self.last_cycle_tab.clear_selection_btn.clicked.connect(self.last_cycle_tab.clear_selection)
        
        self.dependencies_tab.new_data_btn.clicked.connect(self.add_dep_data)
        self.dependencies_tab.sort_hz_btn.clicked.connect(self.sort_dep_on_hz)
        self.dependencies_tab.sort_cl_btn.clicked.connect(self.sort_dep_on_cl)
        self.dependencies_tab.save_btn.clicked.connect(self.save_dep_table_to_excel)
        self.dependencies_tab.draw_chart_btn.clicked.connect(self.draw_dep_chart)
        
        self.integrals_tab.new_data_btn.clicked.connect(self.add_int_data)
        self.integrals_tab.sort_hz_btn.clicked.connect(self.sort_int_on_hz)
        self.integrals_tab.sort_cl_btn.clicked.connect(self.sort_int_on_cl)
        self.integrals_tab.save_btn.clicked.connect(self.save_int_table_to_excel)
        self.integrals_tab.draw_chart_btn.clicked.connect(self.draw_int_chart)
    
    def _create_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')
    
    def show_documentation(self) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        doc_path = os.path.join(base_dir, 'docs', 'manual.html')
        if os.path.exists(doc_path):
            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(doc_path)))
        else:
            QMessageBox.warning(self, 'Documentation', f'Documentation file not found: {doc_path}')
    
    def show_about(self) -> None:
        QMessageBox.about(
            self,
            'About H5 Reader',
            f'<h3>H5 Reader</h3>'
            f'<p>Version {VERSION}</p>'
            f'<p>Author: {AUTHOR}</p>'
            '<p>A program for viewing and analyzing HDF5 files '
            'with cardiomyocyte simulation data.</p>'
            '<p>Features:</p>'
            '<ul>'
            '<li>Open and browse HDF5 files</li>'
            '<li>Plot variables, currents, and forces over time</li>'
            '<li>Analyze APD, calcium, and force characteristics</li>'
            '<li>Calculate integrals for calcium handling</li>'
            '<li>Export data to Excel</li>'
            '</ul>'
            '<p>Keyboard shortcuts:</p>'
            '<ul>'
            '<li>Ctrl+O - Open file</li>'
            '<li>F1 - Documentation</li>'
            '</ul>'
        )
    
    def open_file(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self, 'Open H5 File', '', 'H5 Files (*.h5 *.hdf5)'
        )

        if filepath:
            self.load_file(filepath)

    def load_file(self, filepath: str) -> None:
        try:
            h5file = self.h5_reader.open_file(filepath)
            self.files.append(h5file)
            self.current_file = h5file
            
            item = QListWidgetItem(h5file.filename)
            self.files_list.addItem(item)
            self.files_list.setCurrentItem(item)
            
            self.update_tree()
            self.update_info()
            
            self.status_bar.showMessage(f'Loaded: {h5file.filename}')
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open file: {str(e)}')
    
    def on_file_selected(self, item: QListWidgetItem) -> None:
        idx = self.files_list.row(item)
        if idx < len(self.files):
            self.current_file = self.files[idx]
            self.h5_reader.current_file = self.current_file
            self.update_tree()
            self.update_info()
            self.delete_file_btn.setEnabled(True)
            if self.last_cycle_tab.plot_data:
                self.last_cycle_tab._redraw()
    
    def delete_file(self) -> None:
        current_row = self.files_list.currentRow()
        if current_row >= 0:
            h5file = self.files[current_row]
            self.h5_reader.close_file(h5file)
            self.files.pop(current_row)
            self.files_list.takeItem(current_row)
            
            if self.files:
                self.current_file = self.files[0]
                self.h5_reader.current_file = self.current_file
            else:
                self.current_file = None
                self.tree_widget.clear()
                self.clear_info()
                self.delete_file_btn.setEnabled(False)
    
    def update_tree(self) -> None:
        self.tree_widget.clear()
        
        if not self.current_file:
            return
        
        params = self.h5_reader.get_all_parameters(self.current_file)
        
        for group in self.current_file.groups:
            group_item = QTreeWidgetItem([group, ''])
            self.tree_widget.addTopLevelItem(group_item)
            
            if group in self.current_file.datasets:
                for dataset in self.current_file.datasets[group]:
                    if group == 'parameters' and dataset in params:
                        value = params[dataset]
                        dataset_item = QTreeWidgetItem([dataset, value])
                    else:
                        dataset_item = QTreeWidgetItem([dataset, ''])
                    group_item.addChild(dataset_item)
            
            group_item.setExpanded(True)
    
    def update_info(self) -> None:
        if self.current_file:
            info = []
            if self.current_file.cycle:
                info.append(f'Cycle Length: {self.current_file.cycle}')
            if self.current_file.Herz:
                info.append(f'Frequency (Hz): {self.current_file.Herz:.2f}')
            if self.current_file.count_cycle:
                info.append(f'Numbers of Cycles: {self.current_file.count_cycle}')
            
            self.info_label.setText('\n'.join(info))
    
    def clear_info(self) -> None:
        self.info_label.setText('')
    
    def on_tree_item_clicked(self, item):
        if not self.current_file:
            return
            
        parent = item.parent()
        if parent:
            group = parent.text(0)
            dataset = item.text(0)
            
            if self.tab_widget.currentIndex() == 0:
                self.all_cycles_tab.plot(group, dataset)
            elif self.tab_widget.currentIndex() == 1:
                if group != 'parameters':
                    self.last_cycle_tab.add_selection(group, dataset)
    
    def set_single_mode(self) -> None:
        self.all_cycles_tab.single_mode_btn.setChecked(True)
        self.all_cycles_tab.multiple_mode_btn.setChecked(False)
    
    def set_multiple_mode(self) -> None:
        self.all_cycles_tab.single_mode_btn.setChecked(False)
        self.all_cycles_tab.multiple_mode_btn.setChecked(True)
    
    def toggle_stimuli(self) -> None:
        if not self.current_file or not self.all_cycles_tab.current_plot_data:
            return
        
        time_data = self.all_cycles_tab.current_plot_data.get('time')
        data_data = self.all_cycles_tab.current_plot_data.get('data')
        
        if time_data is None or data_data is None:
            return
        
        cycle = self.current_file.cycle
        start_stim = self.current_file.start_stim if self.current_file.start_stim else 10
        
        if cycle is None:
            return
        
        h_stimuli = None
        for artist in self.all_cycles_tab.canvas.axes.get_children():
            if hasattr(artist, 'get_label') and artist.get_label() == 'Stimuli':
                h_stimuli = artist
                break
        
        if self.all_cycles_tab.show_stimuli_check.isChecked():
            if not h_stimuli:
                highlight_indices = []
                count_cycle = self.current_file.count_cycle if self.current_file.count_cycle else 1
                
                for cycle_num in range(1, count_cycle + 1):
                    start_idx = (cycle_num - 1) * int(cycle) + 1
                    target_idx = start_idx + int(start_stim) - 1
                    if target_idx < len(data_data):
                        highlight_indices.append(target_idx)
                
                if highlight_indices:
                    x_vals = time_data[highlight_indices]
                    y_vals = data_data[highlight_indices]
                    self.all_cycles_tab.canvas.axes.plot(
                        x_vals, y_vals, '^r', markersize=8, 
                        markerfacecolor='r', label='Stimuli'
                    )
                    self.all_cycles_tab.canvas.draw()
        else:
            if h_stimuli:
                h_stimuli.remove()
                self.all_cycles_tab.canvas.draw()

    def add_dep_data(self) -> None:
        if not self.current_file:
            QMessageBox.warning(self, 'Warning', 'No file selected')
            return
        
        fname = self.current_file.filename
        time = self.h5_reader.read_dataset('time', '')
        cycle = self.current_file.cycle
        points_mod = self.current_file.points_mod
        Herz = self.current_file.Herz
        
        tab = self.dependencies_tab
        
        if fname in tab.files:
            QMessageBox.warning(self, 'Existing Data', 'Data is already in the table')
            return
        
        if not tab.characteristics:
            tab.characteristics = [
                'Frequency (Hz)',
                'Cycle length (ms)',
                'Check point',
                'V_max (mV)', 'V_min (mV)', 'V_ampl (mV)', 'tV_max (ms)', 
                'APD_20 (ms)', 'APD_50 (ms)', 'APD_90 (ms)',
                'Lmuscle (mkm)', 'l1_diast (mkm)', 'l1_syst (mkm)', 'l1_diff (mkm)', 'l1_frac (%)',
                'FXSE_max (AFU)', 'FXSE_min (AFU)', 'FXSE_ampl (AFU)', 'tFXSE_max (ms)',
                'FXSE_D50 (ms)', 'FXSE_D70 (ms)', 'FXSE_D90 (ms)',
                'DF_max (AFU/ms)', 'DF_max(norm) (1/ms)', 'DF_min (AFU/ms)', 'DF_min(norm) (1/ms)',
                'Cai_max (mkM)', 'Cai_min (mkM)', 'Cai_ampl (mkM)', 'tCai_max (ms)',
                'Cai_D10 (ms)', 'Cai_D50 (ms)', 'Cai_D70 (ms)', 'Cai_D90 (ms)'
            ]
        
        t_start = int(np.max(time) + 1 - cycle - points_mod)
        
        values = {}
        values['Frequency (Hz)'] = Herz if Herz else 0
        values['Cycle length (ms)'] = cycle if cycle else 0
        values['Check point'] = t_start
        
        try:
            vars_v = self.h5_reader.read_dataset_slice('variables', 'V', t_start, int(cycle) + 1) if cycle else None
            if vars_v is not None:
                ampl_v = np.max(vars_v) - np.min(vars_v)
                tVmax = np.argmax(vars_v) - 10
                
                V20 = 0.8 * ampl_v + np.min(vars_v)
                V50 = 0.5 * ampl_v + np.min(vars_v)
                V90 = 0.1 * ampl_v + np.min(vars_v)
                
                Vup = np.where(vars_v > V20)[0]
                APD20 = Vup[-1] - (tVmax + 10) if len(Vup) > 0 else 0
                Vup = np.where(vars_v > V50)[0]
                APD50 = Vup[-1] - (tVmax + 10) if len(Vup) > 0 else 0
                Vup = np.where(vars_v > V90)[0]
                APD90 = Vup[-1] - (tVmax + 10) if len(Vup) > 0 else 0
                
                values['V_max (mV)'] = np.max(vars_v)
                values['V_min (mV)'] = np.min(vars_v)
                values['V_ampl (mV)'] = ampl_v
                values['tV_max (ms)'] = tVmax
                values['APD_20 (ms)'] = APD20
                values['APD_50 (ms)'] = APD50
                values['APD_90 (ms)'] = APD90
        except Exception as e:
            logger.warning(f"Failed to calculate V characteristics: {e}")

        try:
            vars_l = self.h5_reader.read_dataset_slice('variables', 'l_1', t_start, int(cycle) + 1) if cycle else None
            if vars_l is not None:
                l1_diast = np.max(vars_l)
                l1_syst = np.min(vars_l)
                l1_diff = l1_diast - l1_syst
                l1_frac = 100 - (l1_diff + 1.67) / (l1_diast + 1.67) * 100
                
                values['l1_diast (mkm)'] = l1_diast
                values['l1_syst (mkm)'] = l1_syst
                values['l1_diff (mkm)'] = l1_diff
                values['l1_frac (%)'] = l1_frac
        except Exception as e:
            logger.warning(f"Failed to calculate l_1 characteristics: {e}")

        try:
            vars_f = self.h5_reader.read_dataset_slice('forces', 'F_XSE', t_start, int(cycle) + 1) if cycle else None
            if vars_f is not None:
                ampl_f = np.max(vars_f) - vars_f[10] if len(vars_f) > 10 else 0
                tFmax = np.argmax(vars_f) - 10
                
                values['FXSE_max (AFU)'] = np.max(vars_f)
                values['FXSE_min (AFU)'] = vars_f[10] if len(vars_f) > 10 else 0
                values['FXSE_ampl (AFU)'] = ampl_f
                values['tFXSE_max (ms)'] = tFmax
        except Exception as e:
            logger.warning(f"Failed to calculate FXSE characteristics: {e}")

        try:
            vars_ca = self.h5_reader.read_dataset_slice('variables', 'Ca_i', t_start, int(cycle) + 1) if cycle else None
            if vars_ca is not None:
                ampl_ca = np.max(vars_ca) - vars_ca[10] if len(vars_ca) > 10 else 0
                tCamax = np.argmax(vars_ca) - 10
                
                Ca10 = 0.9 * ampl_ca + np.min(vars_ca)
                Ca50 = 0.5 * ampl_ca + np.min(vars_ca)
                Ca70 = 0.3 * ampl_ca + np.min(vars_ca)
                Ca90 = 0.1 * ampl_ca + np.min(vars_ca)
                
                Caup = np.where(vars_ca > Ca10)[0]
                CaD10 = Caup[-1] - (tCamax + 10) if len(Caup) > 0 else 0
                Caup = np.where(vars_ca > Ca50)[0]
                CaD50 = Caup[-1] - (tCamax + 10) if len(Caup) > 0 else 0
                Caup = np.where(vars_ca > Ca70)[0]
                CaD70 = Caup[-1] - (tCamax + 10) if len(Caup) > 0 else 0
                Caup = np.where(vars_ca > Ca90)[0]
                CaD90 = Caup[-1] - (tCamax + 10) if len(Caup) > 0 else 0
                
                values['Cai_max (mkM)'] = np.max(vars_ca) * 1000
                values['Cai_min (mkM)'] = vars_ca[10] * 1000 if len(vars_ca) > 10 else 0
                values['Cai_ampl (mkM)'] = ampl_ca * 1000
                values['tCai_max (ms)'] = tCamax
                values['Cai_D10 (ms)'] = CaD10
                values['Cai_D50 (ms)'] = CaD50
                values['Cai_D70 (ms)'] = CaD70
                values['Cai_D90 (ms)'] = CaD90
        except Exception as e:
            logger.warning(f"Failed to calculate Cai characteristics: {e}")

        tab.files.append(fname)
        tab.data[fname] = values
        
        tab.update_table()
        tab.enable_controls()
        
        self.status_bar.showMessage(f'Added data for: {fname}')
    
    def sort_dep_on_hz(self) -> None:
        tab = self.dependencies_tab
        if not tab.data:
            return
        
        sorted_files = sorted(tab.files, 
                            key=lambda f: tab.data[f].get('Frequency (Hz)', 0))
        tab.files = sorted_files
        tab.update_table()
        self.status_bar.showMessage('Sorted by Frequency (Hz)')
    
    def sort_dep_on_cl(self) -> None:
        tab = self.dependencies_tab
        if not tab.data:
            return
        
        sorted_files = sorted(tab.files, 
                            key=lambda f: tab.data[f].get('Cycle length (ms)', 0))
        tab.files = sorted_files
        tab.update_table()
        self.status_bar.showMessage('Sorted by Cycle length (ms)')
    
    def draw_dep_chart(self) -> None:
        tab = self.dependencies_tab
        x_axis = tab.x_axis_combo.currentText()
        char = tab.char_combo.currentText()
        
        if not x_axis or not char:
            return
        
        x_vals = []
        y_vals = []
        
        for fname in tab.files:
            x_val = tab.data[fname].get(x_axis, 0)
            y_val = tab.data[fname].get(char, 0)
            x_vals.append(x_val)
            y_vals.append(y_val)
        
        if not x_vals:
            return
        
        tab.canvas.axes.clear()
        tab.canvas.axes.plot(x_vals, y_vals, 'o-', markersize=8)
        tab.canvas.axes.set_xlabel(x_axis)
        tab.canvas.axes.set_ylabel(char)
        tab.canvas.axes.set_title(f'{char} vs {x_axis}')
        tab.canvas.axes.grid(True)
        tab.canvas.draw()
        
        self.status_bar.showMessage(f'Chart: {char} vs {x_axis}')
    
    def save_dep_table_to_excel(self) -> None:
        tab = self.dependencies_tab
        if not tab.data:
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save Dependencies to Excel', '', 'Excel Files (*.xlsx)'
        )
        
        if not filepath:
            return
        
        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'
        
        import pandas as pd
        
        columns = ['Characteristics'] + tab.files
        data = []
        for char in tab.characteristics:
            row = [char]
            for fname in tab.files:
                row.append(tab.data[fname].get(char, ''))
            data.append(row)
        
        df = pd.DataFrame(data, columns=columns)
        df.to_excel(filepath, index=False)
        self.status_bar.showMessage(f'Saved to: {filepath}')
    
    def add_int_data(self) -> None:
        if not self.current_file:
            QMessageBox.warning(self, 'Warning', 'No file selected')
            return
        
        fname = self.current_file.filename
        time = self.h5_reader.read_dataset('time', '')
        cycle = self.current_file.cycle
        points_mod = self.current_file.points_mod
        Herz = self.current_file.Herz
        
        tab = self.integrals_tab
        
        if fname in tab.files:
            QMessageBox.warning(self, 'Existing Data', 'Data is already in the table')
            return
        
        if not tab.characteristics:
            tab.characteristics = [
                'Frequency (Hz)',
                'Cycle length (ms)',
                'Int{i_relSR} (mM)', 'Int{i_relcyt} (mM)', 'Int{i_relSS} (mM)',
                'Int{i_leak} (mM)', 'Int{i_up} (mM)',
                'Int{i_xfercyt} (mM)', 'Int{i_xferSS} (mM)',
                'Int{i_bCa} (mM)', 'Int{i_pCa} (mM)',
                'Int{i_NaCain} (mM)', 'Int{i_NaCaout} (mM)', 'Int{i_NaCatotal} (mM)',
                'Int{i_CaLcyt} (mM)', 'Int{i_CaLSS} (mM)',
                'Int{CaTnC} (mM)', 'Int{Buffc} (mM)', 'Int{Cain_total} (mM)'
            ]
        
        t_start = int(np.max(time) + 1 - cycle - points_mod) if cycle else 0
        ht = time[1] - time[0] if len(time) > 1 else 0.1
        
        values = {}
        values['Frequency (Hz)'] = Herz if Herz else 0
        values['Cycle length (ms)'] = cycle if cycle else 0
        
        try:
            VjSR = float(self.current_file.fid['/parameters/V_jSR'][()]) if '/parameters/V_jSR' in self.current_file.fid else 0.01
            Vc = float(self.current_file.fid['/parameters/V_c'][()]) if '/parameters/V_c' in self.current_file.fid else 0.02
            Vss = float(self.current_file.fid['/parameters/V_ss'][()]) if '/parameters/V_ss' in self.current_file.fid else 0.001
            FF = float(self.current_file.fid['/parameters/F'][()]) if '/parameters/F' in self.current_file.fid else 96485
            CC = float(self.current_file.fid['/parameters/Cm'][()]) if '/parameters/Cm' in self.current_file.fid else 1.0
            
            def calc_integral(current, coeff):
                return np.sum(current[:int(cycle)+1]) * ht * coeff if cycle else 0
            
            try:
                irel = self.h5_reader.read_dataset_slice('currents', 'i_rel', t_start, int(cycle) + 1) if cycle else None
                if irel is not None:
                    values['Int{i_relSR} (mM)'] = calc_integral(irel, 1)
                    values['Int{i_relcyt} (mM)'] = calc_integral(irel, VjSR / Vc)
                    values['Int{i_relSS} (mM)'] = calc_integral(irel, VjSR / Vss)
            except Exception as e:
                logger.warning(f"Failed to calculate i_rel integrals: {e}")
                values['Int{i_relSR} (mM)'] = 0
                values['Int{i_relcyt} (mM)'] = 0
                values['Int{i_relSS} (mM)'] = 0

            try:
                ileak = self.h5_reader.read_dataset_slice('currents', 'i_leak', t_start, int(cycle) + 1) if cycle else None
                values['Int{i_leak} (mM)'] = calc_integral(ileak, 1) if ileak is not None else 0
            except Exception as e:
                logger.warning(f"Failed to calculate i_leak integral: {e}")
                values['Int{i_leak} (mM)'] = 0

            try:
                iup = self.h5_reader.read_dataset_slice('currents', 'i_up', t_start, int(cycle) + 1) if cycle else None
                values['Int{i_up} (mM)'] = calc_integral(iup, 1) if iup is not None else 0
            except Exception as e:
                logger.warning(f"Failed to calculate i_up integral: {e}")
                values['Int{i_up} (mM)'] = 0

            try:
                ixfer = self.h5_reader.read_dataset_slice('currents', 'i_xfer', t_start, int(cycle) + 1) if cycle else None
                if ixfer is not None:
                    values['Int{i_xfercyt} (mM)'] = calc_integral(ixfer, 1)
                    values['Int{i_xferSS} (mM)'] = calc_integral(ixfer, Vc / Vss)
                else:
                    values['Int{i_xfercyt} (mM)'] = 0
                    values['Int{i_xferSS} (mM)'] = 0
            except Exception as e:
                logger.warning(f"Failed to calculate i_xfer integrals: {e}")
                values['Int{i_xfercyt} (mM)'] = 0
                values['Int{i_xferSS} (mM)'] = 0

            try:
                ibCa = self.h5_reader.read_dataset_slice('currents', 'i_b_Ca', t_start, int(cycle) + 1) if cycle else None
                values['Int{i_bCa} (mM)'] = calc_integral(ibCa, CC / (2 * Vc * FF)) if ibCa is not None else 0
            except Exception as e:
                logger.warning(f"Failed to calculate i_b_Ca integral: {e}")
                values['Int{i_bCa} (mM)'] = 0

            try:
                ipCa = self.h5_reader.read_dataset_slice('currents', 'i_p_Ca', t_start, int(cycle) + 1) if cycle else None
                values['Int{i_pCa} (mM)'] = calc_integral(ipCa, CC / (2 * Vc * FF)) if ipCa is not None else 0
            except Exception as e:
                logger.warning(f"Failed to calculate i_p_Ca integral: {e}")
                values['Int{i_pCa} (mM)'] = 0

            try:
                iNaCa = self.h5_reader.read_dataset_slice('currents', 'i_NaCa', t_start, int(cycle) + 1) if cycle else None
                if iNaCa is not None:
                    ina_in = np.sum(iNaCa[iNaCa < 0] * ht * CC / (Vc * FF)) if cycle else 0
                    ina_out = np.sum(iNaCa[iNaCa > 0] * ht * CC / (Vc * FF)) if cycle else 0
                    values['Int{i_NaCain} (mM)'] = abs(ina_in)
                    values['Int{i_NaCaout} (mM)'] = ina_out
                    values['Int{i_NaCatotal} (mM)'] = np.sum(iNaCa * ht * CC / (Vc * FF)) if cycle else 0
                else:
                    values['Int{i_NaCain} (mM)'] = 0
                    values['Int{i_NaCaout} (mM)'] = 0
                    values['Int{i_NaCatotal} (mM)'] = 0
            except Exception as e:
                logger.warning(f"Failed to calculate i_NaCa integrals: {e}")
                values['Int{i_NaCain} (mM)'] = 0
                values['Int{i_NaCaout} (mM)'] = 0
                values['Int{i_NaCatotal} (mM)'] = 0

            try:
                iCaL = self.h5_reader.read_dataset_slice('currents', 'i_CaL', t_start, int(cycle) + 1) if cycle else None
                if iCaL is not None:
                    values['Int{i_CaLcyt} (mM)'] = calc_integral(iCaL, CC / (2 * Vc * FF))
                    values['Int{i_CaLSS} (mM)'] = calc_integral(iCaL, CC / (2 * Vss * FF))
                else:
                    values['Int{i_CaLcyt} (mM)'] = 0
                    values['Int{i_CaLSS} (mM)'] = 0
            except Exception as e:
                logger.warning(f"Failed to calculate i_CaL integrals: {e}")
                values['Int{i_CaLcyt} (mM)'] = 0
                values['Int{i_CaLSS} (mM)'] = 0
            
            values['Int{CaTnC} (mM)'] = 0
            values['Int{Buffc} (mM)'] = 0
            values['Int{Cain_total} (mM)'] = 0
            
        except Exception as e:
            for char in tab.characteristics[2:]:
                if char not in values:
                    values[char] = 0
        
        for char in tab.characteristics:
            if char not in values:
                values[char] = 0
        
        tab.files.append(fname)
        tab.data[fname] = values
        
        tab.update_table()
        tab.enable_controls()
        
        self.status_bar.showMessage(f'Added integrals for: {fname}')
    
    def sort_int_on_hz(self) -> None:
        tab = self.integrals_tab
        if not tab.data:
            return
        
        sorted_files = sorted(tab.files, 
                            key=lambda f: tab.data[f].get('Frequency (Hz)', 0))
        tab.files = sorted_files
        tab.update_table()
        self.status_bar.showMessage('Sorted by Frequency (Hz)')
    
    def sort_int_on_cl(self) -> None:
        tab = self.integrals_tab
        if not tab.data:
            return
        
        sorted_files = sorted(tab.files, 
                            key=lambda f: tab.data[f].get('Cycle length (ms)', 0))
        tab.files = sorted_files
        tab.update_table()
        self.status_bar.showMessage('Sorted by Cycle length (ms)')
    
    def draw_int_chart(self) -> None:
        tab = self.integrals_tab
        x_axis = tab.x_axis_combo.currentText()
        char = tab.integrals_combo.currentText()
        
        if not x_axis or not char:
            return
        
        x_vals = []
        y_vals = []
        
        for fname in tab.files:
            x_val = tab.data[fname].get(x_axis, 0)
            y_val = tab.data[fname].get(char, 0)
            x_vals.append(x_val)
            y_vals.append(y_val)
        
        if not x_vals:
            return
        
        tab.canvas.axes.clear()
        tab.canvas.axes.plot(x_vals, y_vals, 'o-', markersize=8)
        tab.canvas.axes.set_xlabel(x_axis)
        tab.canvas.axes.set_ylabel(char)
        tab.canvas.axes.set_title(f'{char} vs {x_axis}')
        tab.canvas.axes.grid(True)
        tab.canvas.draw()
        
        self.status_bar.showMessage(f'Chart: {char} vs {x_axis}')
    
    def save_int_table_to_excel(self) -> None:
        tab = self.integrals_tab
        if not tab.data:
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save Integrals to Excel', '', 'Excel Files (*.xlsx)'
        )
        
        if not filepath:
            return
        
        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'
        
        import pandas as pd
        
        columns = ['Integrals'] + tab.files
        data = []
        for char in tab.characteristics:
            row = [char]
            for fname in tab.files:
                row.append(tab.data[fname].get(char, ''))
            data.append(row)
        
        df = pd.DataFrame(data, columns=columns)
        df.to_excel(filepath, index=False)
        self.status_bar.showMessage(f'Saved to: {filepath}')
    
    def save_all_cycles(self) -> None:
        if not self.current_file:
            QMessageBox.warning(self, 'Warning', 'No file selected')
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save All Cycles', '', 'Excel Files (*.xlsx)'
        )
        
        if not filepath:
            return
        
        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'
        
        time = self.h5_reader.read_dataset('time', '')
        
        if time is None:
            QMessageBox.warning(self, 'Error', 'No time data')
            return
        
        import pandas as pd
        
        data = {'time (ms)': time}
        
        for group in self.current_file.groups:
            if group in self.current_file.datasets:
                for dataset in self.current_file.datasets[group]:
                    try:
                        d = self.h5_reader.read_dataset(group, dataset)
                        if d is not None and len(d) == len(time):
                            data[f'{group}/{dataset}'] = d
                    except Exception as e:
                        logger.warning(f"Failed to read {group}/{dataset}: {e}")
        
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False)
        self.status_bar.showMessage(f'Saved all cycles to: {filepath}')
    
    def save_first_cycle(self) -> None:
        if not self.current_file:
            QMessageBox.warning(self, 'Warning', 'No file selected')
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save First Cycle', '', 'Excel Files (*.xlsx)'
        )

        if not filepath:
            return

        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'

        time = self.h5_reader.read_dataset('time', '')
        cycle = self.current_file.cycle

        if time is None or cycle is None:
            QMessageBox.warning(self, 'Error', 'No data')
            return

        import pandas as pd

        cycle_len = int(cycle) + 1
        t = time[:cycle_len]

        data = {'time (ms)': t}

        for group in self.current_file.groups:
            if group in self.current_file.datasets:
                for dataset in self.current_file.datasets[group]:
                    try:
                        d = self.h5_reader.read_dataset(group, dataset)
                        if d is not None and len(d) >= cycle_len:
                            data[f'{group}/{dataset}'] = d[:cycle_len]
                    except Exception as e:
                        logger.warning(f"Failed to read {group}/{dataset}: {e}")

        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False)
        self.status_bar.showMessage(f'Saved first cycle to: {filepath}')
    
    def save_last_cycle(self) -> None:
        if not self.current_file:
            QMessageBox.warning(self, 'Warning', 'No file selected')
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save Last Cycle', '', 'Excel Files (*.xlsx)'
        )
        
        if not filepath:
            return
        
        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'
        
        time = self.h5_reader.read_dataset('time', '')
        cycle = self.current_file.cycle
        points_mod = self.current_file.points_mod
        
        if time is None or cycle is None:
            QMessageBox.warning(self, 'Error', 'No data')
            return
        
        import pandas as pd
        
        t_start = int(np.max(time) + 1 - cycle - points_mod)
        t_end = int(np.max(time) + 1 - points_mod)
        
        min_len = min(len(time), t_end + 1) - t_start
        t = time[t_start:t_start + min_len]
        
        data = {'time (ms)': t}
        
        for group in self.current_file.groups:
            if group in self.current_file.datasets:
                for dataset in self.current_file.datasets[group]:
                    try:
                        d = self.h5_reader.read_dataset(group, dataset)
                        if d is not None and len(d) >= t_start + min_len:
                            data[f'{group}/{dataset}'] = d[t_start:t_start + min_len]
                    except Exception as e:
                        logger.warning(f"Failed to read {group}/{dataset}: {e}")

        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False)
        self.status_bar.showMessage(f'Saved last cycle to: {filepath}')

    def save_parameters(self) -> None:
        if not self.current_file:
            QMessageBox.warning(self, 'Warning', 'No file selected')
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save Parameters', '', 'Excel Files (*.xlsx)'
        )

        if not filepath:
            return

        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'

        import pandas as pd

        params = []

        try:
            time = self.h5_reader.read_dataset('time', '')
            if time is not None:
                params.append(('max(time)', float(np.max(time)), 'time'))
        except Exception as e:
            logger.warning(f"Failed to read time data: {e}")
        
        if self.current_file.cycle:
            params.append(('stim_period (ms)', self.current_file.cycle, 'calculated'))
        if self.current_file.start_stim:
            params.append(('stim_start (ms)', self.current_file.start_stim, 'calculated'))
        if self.current_file.Herz:
            params.append(('Frequency (Hz)', self.current_file.Herz, 'calculated'))
        if self.current_file.count_cycle:
            params.append(('Number of cycles', self.current_file.count_cycle, 'calculated'))
        if self.current_file.points_mod is not None:
            params.append(('points_mod', self.current_file.points_mod, 'calculated'))
        
        for group in self.current_file.datasets:
            if group == 'parameters':
                for dataset in self.current_file.datasets[group]:
                    try:
                        d = self.current_file.fid[f'/parameters/{dataset}'][()]
                        try:
                            params.append((dataset, float(d), 'parameter'))
                        except Exception as e:
                            logger.debug(f"Could not convert {dataset} to float: {e}")
                            params.append((dataset, str(d), 'parameter'))
                    except Exception as e:
                        logger.warning(f"Failed to read parameter {dataset}: {e}")
                        params.append((dataset, f'Error', 'error'))
        
        df = pd.DataFrame({'Parameter': [p[0] for p in params], 
                         'Value': [p[1] for p in params],
                         'Type': [p[2] for p in params]})
        df.to_excel(filepath, index=False)
        self.status_bar.showMessage(f'Saved {len(params)} parameters to: {filepath}')
    
    def save_vars(self) -> None:
        if not self.current_file:
            QMessageBox.warning(self, 'Warning', 'No file selected')
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save Vars (1st and Last values)', '', 'Excel Files (*.xlsx)'
        )
        
        if not filepath:
            return
        
        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'
        
        import pandas as pd
        
        time = self.h5_reader.read_dataset('time', '')
        cycle = self.current_file.cycle
        points_mod = self.current_file.points_mod
        
        first_values = {}
        last_cycle_values = {}
        
        if time is not None and cycle is not None:
            t_start = int(np.max(time) + 1 - cycle - points_mod)
            t_end = int(np.max(time) + 1 - points_mod)
            last_cycle_len = t_end - t_start + 1
        else:
            last_cycle_len = 0
        
        for group in self.current_file.datasets:
            if group in ['variables', 'currents', 'forces']:
                for dataset in self.current_file.datasets[group]:
                    try:
                        d = self.h5_reader.read_dataset(group, dataset)
                        if d is not None and len(d) > 0:
                            first_values[f'{group}/{dataset}'] = float(d[0])
                            
                            if last_cycle_len > 0 and len(d) >= t_start + last_cycle_len:
                                last_cycle_values[f'{group}/{dataset}'] = float(d[t_start + last_cycle_len - 1])
                            elif len(d) > 0:
                                last_cycle_values[f'{group}/{dataset}'] = float(d[-1])
                    except Exception as e:
                        logger.warning(f"Failed to read {group}/{dataset}: {e}")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df_first = pd.DataFrame({
                'Variable': list(first_values.keys()),
                'First Value': list(first_values.values())
            })
            df_first.to_excel(writer, sheet_name='First Values', index=False)
            
            df_last = pd.DataFrame({
                'Variable': list(last_cycle_values.keys()),
                'Last Cycle Value': list(last_cycle_values.values())
            })
            df_last.to_excel(writer, sheet_name='Last Values', index=False)
            
            info = []
            if self.current_file.cycle:
                info.append(('Cycle length (ms)', self.current_file.cycle))
            if self.current_file.count_cycle:
                info.append(('Number of cycles', self.current_file.count_cycle))
            if self.current_file.Herz:
                info.append(('Frequency (Hz)', self.current_file.Herz))
          
            if info:
                df_info = pd.DataFrame(info, columns=['Parameter', 'Value'])
                df_info.to_excel(writer, sheet_name='Info', index=False)
        
        self.status_bar.showMessage(f'Saved vars to: {filepath}')
    
    def save_charts(self) -> None:
        if not self.current_file:
            QMessageBox.warning(self, 'Warning', 'No file selected')
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save Charts to XLS', '', 'Excel Files (*.xlsx)'
        )
        
        if not filepath:
            return
        
        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'
        
        import pandas as pd
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        
        time = self.h5_reader.read_dataset('time', '')
        cycle = self.current_file.cycle
        points_mod = self.current_file.points_mod
        
        if time is None or cycle is None:
            QMessageBox.warning(self, 'Error', 'No data')
            return
        
        t_start = int(np.max(time) + 1 - cycle - points_mod)
        t_end = int(np.max(time) + 1 - points_mod)
        
        min_len = min(len(time), t_end + 1) - t_start
        t = time[t_start:t_start + min_len]
        
        pdf_path = filepath.replace('.xlsx', '_charts.pdf')
        
        with PdfPages(pdf_path) as pdf:
            groups_to_plot = ['variables', 'currents', 'forces']
            
            for group in groups_to_plot:
                if group not in self.current_file.datasets:
                    continue
                    
                for dataset in self.current_file.datasets[group]:
                    try:
                        d = self.h5_reader.read_dataset(group, dataset)
                        if d is not None and len(d) >= t_start + min_len:
                            data_cycle = d[t_start:t_start + min_len]
                            
                            fig, ax = plt.subplots(figsize=(10, 6))
                            ax.plot(t, data_cycle, 'b-', linewidth=1)
                            ax.set_xlabel('time (ms)')
                            ax.set_title(f'{dataset} ({group})')
                            ax.grid(True, alpha=0.3)

                            pdf.savefig(fig)
                            plt.close(fig)
                    except Exception as e:
                        logger.warning(f"Failed to save chart {group}/{dataset}: {e}")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            info = []
            if self.current_file.cycle:
                info.append(('Cycle length (ms)', self.current_file.cycle))
            if self.current_file.Herz:
                info.append(('Frequency (Hz)', self.current_file.Herz))
            if self.current_file.count_cycle:
                info.append(('Number of cycles', self.current_file.count_cycle))
            
            if info:
                df_info = pd.DataFrame(info, columns=['Parameter', 'Value'])
                df_info.to_excel(writer, sheet_name='Info', index=False)
                
            df_link = pd.DataFrame({
                'Charts saved to PDF': [pdf_path],
                'Location': 'Same folder as Excel file'
            })
            df_link.to_excel(writer, sheet_name='Charts', index=False)
        
        self.status_bar.showMessage(f'Saved charts to: {pdf_path}')
    
    def ssh_connect(self) -> None:
        dialog = SSHDialog(self)
        if dialog.exec():
            host, port, username, password, key_file, download_dir = dialog.get_connection_params()
            if not host or not username:
                QMessageBox.warning(self, 'Error', 'Host and username are required')
                return
            
            self.status_bar.showMessage(f'Connecting to {host}...')
            
            result = self.ssh_connection.connect(host, port, username, password, key_file, timeout=15)
            
            if result:
                self.download_dir = download_dir
                self.status_bar.showMessage(f'Connected to {host} ({username}@{host}:{port})')
                QMessageBox.information(self, 'Connected', f'Successfully connected to {host}')
            else:
                error_msg = self.ssh_connection.last_error if self.ssh_connection.last_error else 'Unknown error'
                self.status_bar.showMessage('Connection failed')
                QMessageBox.critical(self, 'Error', f'Failed to connect to SSH server.\n\nError: {error_msg}')
    
    def ssh_disconnect(self) -> None:
        if self.ssh_connection.is_connected():
            self.ssh_connection.disconnect()
            self.status_bar.showMessage('Disconnected from SSH server')
            QMessageBox.information(self, 'Disconnected', 'SSH connection closed')
        else:
            QMessageBox.information(self, 'Info', 'No active SSH connection')
    
    def ssh_browse(self) -> None:
        if not self.ssh_connection.is_connected():
            reply = QMessageBox.question(
                self, 'Not Connected', 
                'Not connected to SSH. Would you like to connect now?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.ssh_connect()
                if not self.ssh_connection.is_connected():
                    return
        
        dialog = QDialog(self)
        dialog.setWindowTitle('SSH File Browser')
        dialog.setMinimumSize(800, 500)
        layout = QVBoxLayout(dialog)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel('Path:'))
        path_input = QLineEdit('/home/')
        path_layout.addWidget(path_input)
        
        up_btn = QPushButton('↑ Up')
        up_btn.clicked.connect(lambda: self._ssh_go_up(dialog, path_input))
        path_layout.addWidget(up_btn)
        
        refresh_btn = QPushButton('↻')
        refresh_btn.setToolTip('Refresh')
        refresh_btn.clicked.connect(lambda: self._ssh_refresh(dialog, path_input))
        path_layout.addWidget(refresh_btn)
        
        layout.addLayout(path_layout)
        
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(['Name', 'Size', 'Type'])
        table.setColumnWidth(0, 400)
        table.setColumnWidth(1, 100)
        table.setColumnWidth(2, 80)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.itemDoubleClicked.connect(lambda item: self._ssh_on_double_click(item, dialog, path_input, table))
        layout.addWidget(table)
        
        self._ssh_load_directory(path_input.text(), table)
        
        btn_layout = QHBoxLayout()
        
        download_btn = QPushButton('Download & Open')
        download_btn.clicked.connect(lambda: self._ssh_download_selected(dialog, path_input.text(), table))
        btn_layout.addWidget(download_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def _ssh_go_up(self, dialog: QDialog, path_input: QLineEdit) -> None:
        current_path = path_input.text()
        if current_path == '/':
            return
        parent = os.path.dirname(current_path)
        if not parent:
            parent = '/'
        path_input.setText(parent)
        table = dialog.findChild(QTableWidget)
        if table:
            self._ssh_load_directory(parent, table)
    
    def _ssh_refresh(self, dialog: QDialog, path_input: QLineEdit) -> None:
        table = dialog.findChild(QTableWidget)
        if table:
            self._ssh_load_directory(path_input.text(), table)
    
    def _ssh_on_double_click(self, item: QTableWidgetItem, dialog: QDialog, path_input: QLineEdit, table: QTableWidget) -> None:
        row = item.row()
        name_item = table.item(row, 0)
        type_item = table.item(row, 2)
        if name_item and type_item:
            name = name_item.text()
            ftype = type_item.text()
            if ftype == 'DIR':
                current_path = path_input.text()
                if current_path.endswith('/'):
                    new_path = current_path + name
                else:
                    new_path = current_path + '/' + name
                path_input.setText(new_path)
                self._ssh_load_directory(new_path, table)
    
    def _ssh_load_directory(self, path: str, table: QTableWidget) -> None:
        files = self.ssh_connection.list_directory_attr(path)
        table.setRowCount(0)
        
        if not files:
            return
        
        dirs = []
        reg_files = []
        
        for f in files:
            fname = f.filename
            if fname.startswith('.'):
                continue
            is_dir = f.st_mode & 0o170000 == 0o040000
            size = f.st_size
            if is_dir:
                dirs.append((fname, size))
            else:
                if fname.endswith('.h5') or fname.endswith('.hdf5'):
                    reg_files.append((fname, size))
        
        all_items = sorted(dirs) + sorted(reg_files)
        
        for fname, size in all_items:
            is_dir = fname in [d[0] for d in dirs]
            row = table.rowCount()
            table.insertRow(row)
            
            name_item = QTableWidgetItem(fname)
            table.setItem(row, 0, name_item)
            
            size_str = self._format_size(size)
            table.setItem(row, 1, QTableWidgetItem(size_str))
            
            ftype = 'DIR' if is_dir else 'FILE'
            table.setItem(row, 2, QTableWidgetItem(ftype))
    
    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def _ssh_download_selected(self, dialog: QDialog, current_path: str, table: QTableWidget) -> None:
        selected_rows = table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, 'Error', 'No file selected')
            return
        
        row = selected_rows[0].row()
        name_item = table.item(row, 0)
        type_item = table.item(row, 2)
        
        if not name_item or not type_item:
            return
        
        filename = name_item.text()
        ftype = type_item.text()
        
        if ftype == 'DIR':
            QMessageBox.warning(self, 'Error', 'Cannot download directory')
            return
        
        if not filename.endswith('.h5') and not filename.endswith('.hdf5'):
            reply = QMessageBox.question(
                self, 'Warning',
                f'File {filename} may not be an H5 file. Download anyway?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        remote_path = f"{current_path}/{filename}" if not current_path.endswith('/') else f"{current_path}{filename}"
        
        if self.download_dir:
            local_path = os.path.join(self.download_dir, filename)
        else:
            local_path = os.path.join(self.temp_dir, filename)
        
        self.status_bar.showMessage(f'Downloading {filename}...')
        dialog.close()
        QApplication.processEvents()
        
        try:
            self.ssh_connection.sftp.get(remote_path, local_path)
            self.status_bar.showMessage(f'Downloaded {filename}')
            self.open_file_local(local_path)
        except Exception as e:
            self.status_bar.showMessage(f'Download failed: {str(e)}')
            QMessageBox.critical(self, 'Error', f'Failed to download: {str(e)}')
    
    def open_file_local(self, path: str) -> None:
        try:
            h5file = self.h5_reader.open_file(path)
            if h5file:
                self.files.append(h5file)
                self.files_list.addItem(h5file.filename)
                self.current_file = h5file
                self.h5_reader.current_file = h5file
                self.update_tree()
                self.update_info()
                self.status_bar.showMessage(f'Opened: {h5file.filename}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open file: {str(e)}')


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
