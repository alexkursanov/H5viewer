from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QMenuBar, QMenu, QFileDialog, QMessageBox, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QSplitter, QFrame,
    QToolBar, QStatusBar, QComboBox, QSlider
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import logging

logger = logging.getLogger(__name__)

from ..core.h5_reader import H5Reader, H5File


class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent: Optional[QWidget] = None, width: float = 6, height: float = 4, dpi: int = 100) -> None:
        self.fig: Figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.h5_reader: H5Reader = H5Reader()
        self.current_file: Optional[H5File] = None
        self.files: List[H5File] = []
        self.current_plot_data: Dict[str, Any] = {}
        self.last_cycle_selected_items: List[QTreeWidgetItem] = []
        self.last_cycle_plots: List[tuple] = []
        self.last_cycle_ylims: List[float] = [float('inf'), float('-inf')]
        self.last_cycle_xlims: List[float] = [0, 0]

        self.dep_data: Dict[str, Dict[str, float]] = {}
        self.dep_characteristics: List[str] = []
        self.dep_files: List[str] = []

        self.int_data: Dict[str, Dict[str, float]] = {}
        self.int_characteristics: List[str] = []
        self.int_files: List[str] = []
        self.setup_ui()

    def setup_ui(self) -> None:
        self.setWindowTitle('H5 Reader')
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
        self.tree_widget.setHeaderLabel('Structure')
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        layout.addWidget(self.tree_widget)
        
        self.info_label = QLabel()
        layout.addWidget(self.info_label)
        
        return frame
    
    def _create_right_panel(self) -> QWidget:
        self.tab_widget = QTabWidget()
        
        self.all_cycles_tab = self._create_all_cycles_tab()
        self.last_cycle_tab = self._create_last_cycle_tab()
        self.dependencies_tab = self._create_dependencies_tab()
        self.integrals_tab = self._create_integrals_tab()
        
        self.tab_widget.addTab(self.all_cycles_tab, 'All Cycles')
        self.tab_widget.addTab(self.last_cycle_tab, 'Last Cycle')
        self.tab_widget.addTab(self.dependencies_tab, 'Dependencies')
        self.tab_widget.addTab(self.integrals_tab, 'Integrals')
        
        return self.tab_widget
    
    def _create_all_cycles_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        
        self.mode_switch_label = QLabel('Mode:')
        toolbar_layout.addWidget(self.mode_switch_label)
        
        self.single_mode_btn = QPushButton('Single')
        self.single_mode_btn.setCheckable(True)
        self.single_mode_btn.setChecked(True)
        self.single_mode_btn.clicked.connect(self.set_single_mode)
        toolbar_layout.addWidget(self.single_mode_btn)
        
        self.multiple_mode_btn = QPushButton('Multiple')
        self.multiple_mode_btn.setCheckable(True)
        self.multiple_mode_btn.clicked.connect(self.set_multiple_mode)
        toolbar_layout.addWidget(self.multiple_mode_btn)
        
        toolbar_layout.addStretch()
        
        self.show_stimuli_check = QPushButton('Show Stimuli')
        self.show_stimuli_check.setCheckable(True)
        self.show_stimuli_check.clicked.connect(self.toggle_stimuli)
        toolbar_layout.addWidget(self.show_stimuli_check)
        
        self.clear_chart_btn = QPushButton('Clear Chart')
        self.clear_chart_btn.clicked.connect(self.clear_all_cycles_chart)
        toolbar_layout.addWidget(self.clear_chart_btn)
        
        layout.addWidget(toolbar)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.all_cycles_canvas = MatplotlibCanvas(widget)
        self.all_cycles_toolbar = NavigationToolbar(self.all_cycles_canvas, widget)
        splitter.addWidget(self.all_cycles_toolbar)
        splitter.addWidget(self.all_cycles_canvas)
        
        sliders_widget = QWidget()
        sliders_layout = QVBoxLayout(sliders_widget)
        
        sliders_layout.addWidget(QLabel('X-Axis Range:'))
        
        up_slider_row = QWidget()
        up_slider_row_layout = QHBoxLayout(up_slider_row)
        up_slider_row_layout.setContentsMargins(0, 0, 0, 0)
        up_slider_row_layout.addWidget(QLabel('Up:'))
        self.up_slider = QSlider(Qt.Orientation.Horizontal)
        self.up_slider.setMinimum(0)
        self.up_slider.setMaximum(100)
        self.up_slider.setValue(0)
        self.up_slider.valueChanged.connect(self.update_x_range)
        up_slider_row_layout.addWidget(self.up_slider)
        self.up_slider_value = QLabel('0')
        up_slider_row_layout.addWidget(self.up_slider_value)
        sliders_layout.addWidget(up_slider_row)
        
        down_slider_row = QWidget()
        down_slider_row_layout = QHBoxLayout(down_slider_row)
        down_slider_row_layout.setContentsMargins(0, 0, 0, 0)
        down_slider_row_layout.addWidget(QLabel('Down:'))
        self.down_slider = QSlider(Qt.Orientation.Horizontal)
        self.down_slider.setMinimum(0)
        self.down_slider.setMaximum(100)
        self.down_slider.setValue(100)
        self.down_slider.valueChanged.connect(self.update_x_range)
        down_slider_row_layout.addWidget(self.down_slider)
        self.down_slider_value = QLabel('100')
        down_slider_row_layout.addWidget(self.down_slider_value)
        sliders_layout.addWidget(down_slider_row)
        
        self.current_plot_data = {}
        
        splitter.addWidget(sliders_widget)
        
        layout.addWidget(splitter)
        
        return widget
    
    def _create_last_cycle_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel('Select items in tree (up to 7), then click Add Lines:'))
        
        self.last_cycle_selected_list = QListWidget()
        self.last_cycle_selected_list.setMaximumHeight(80)
        layout.addWidget(self.last_cycle_selected_list)
        
        selection_btns = QHBoxLayout()
        
        self.remove_selected_btn = QPushButton('Remove Selected')
        self.remove_selected_btn.setEnabled(False)
        self.remove_selected_btn.clicked.connect(self.remove_selected_item)
        selection_btns.addWidget(self.remove_selected_btn)
        
        self.clear_selection_btn = QPushButton('Clear Selection')
        self.clear_selection_btn.setEnabled(False)
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        selection_btns.addWidget(self.clear_selection_btn)
        
        selection_btns.addStretch()
        layout.addLayout(selection_btns)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.last_cycle_canvas = MatplotlibCanvas(widget)
        self.last_cycle_toolbar = NavigationToolbar(self.last_cycle_canvas, widget)
        splitter.addWidget(self.last_cycle_toolbar)
        splitter.addWidget(self.last_cycle_canvas)
        
        layout.addWidget(splitter)
        
        btn_layout = QHBoxLayout()
        
        self.add_lines_btn = QPushButton('Add Lines')
        self.add_lines_btn.clicked.connect(self.add_lines)
        self.add_lines_btn.setEnabled(False)
        btn_layout.addWidget(self.add_lines_btn)
        
        self.total_clear_btn = QPushButton('Total Clear')
        self.total_clear_btn.clicked.connect(self.clear_last_cycle)
        self.total_clear_btn.setEnabled(False)
        btn_layout.addWidget(self.total_clear_btn)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def _create_dependencies_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        left = QWidget()
        left_layout = QVBoxLayout(left)
        
        left_layout.addWidget(QLabel('Data Table:'))
        
        self.dep_table = QTableWidget()
        left_layout.addWidget(self.dep_table)
        
        btn_row = QWidget()
        btn_row_layout = QHBoxLayout(btn_row)
        
        self.new_dep_data_btn = QPushButton('New Data')
        self.new_dep_data_btn.clicked.connect(self.add_dep_data)
        btn_row_layout.addWidget(self.new_dep_data_btn)
        
        self.sort_dep_hz_btn = QPushButton('Sort on Hz')
        self.sort_dep_hz_btn.setEnabled(False)
        self.sort_dep_hz_btn.clicked.connect(self.sort_dep_on_hz)
        btn_row_layout.addWidget(self.sort_dep_hz_btn)
        
        self.sort_dep_cl_btn = QPushButton('Sort on CL')
        self.sort_dep_cl_btn.setEnabled(False)
        self.sort_dep_cl_btn.clicked.connect(self.sort_dep_on_cl)
        btn_row_layout.addWidget(self.sort_dep_cl_btn)
        
        self.save_dep_table_btn = QPushButton('Save to XLS')
        self.save_dep_table_btn.setEnabled(False)
        self.save_dep_table_btn.clicked.connect(self.save_dep_table_to_excel)
        btn_row_layout.addWidget(self.save_dep_table_btn)
        
        left_layout.addWidget(btn_row)
        
        layout.addWidget(left, 1)
        
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        
        controls_layout.addWidget(QLabel('X Axis:'))
        self.x_axis_dep_combo = QComboBox()
        controls_layout.addWidget(self.x_axis_dep_combo)
        
        controls_layout.addWidget(QLabel('Characteristics:'))
        self.char_dep_combo = QComboBox()
        controls_layout.addWidget(self.char_dep_combo)
        
        self.draw_dep_chart_btn = QPushButton('Draw Chart')
        self.draw_dep_chart_btn.setEnabled(False)
        self.draw_dep_chart_btn.clicked.connect(self.draw_dep_chart)
        controls_layout.addWidget(self.draw_dep_chart_btn)
        
        right_layout.addWidget(controls)
        
        self.dep_chart_canvas = MatplotlibCanvas(widget)
        self.dep_chart_toolbar = NavigationToolbar(self.dep_chart_canvas, widget)
        right_layout.addWidget(self.dep_chart_toolbar)
        right_layout.addWidget(self.dep_chart_canvas)
        
        layout.addWidget(right, 2)
        
        return widget
    
    def _create_integrals_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        left = QWidget()
        left_layout = QVBoxLayout(left)
        
        left_layout.addWidget(QLabel('Integrals Table:'))
        
        self.int_table = QTableWidget()
        left_layout.addWidget(self.int_table)
        
        btn_row = QWidget()
        btn_row_layout = QHBoxLayout(btn_row)
        
        self.new_int_data_btn = QPushButton('New Data')
        self.new_int_data_btn.clicked.connect(self.add_int_data)
        btn_row_layout.addWidget(self.new_int_data_btn)
        
        self.sort_int_hz_btn = QPushButton('Sort on Hz')
        self.sort_int_hz_btn.setEnabled(False)
        self.sort_int_hz_btn.clicked.connect(self.sort_int_on_hz)
        btn_row_layout.addWidget(self.sort_int_hz_btn)
        
        self.sort_int_cl_btn = QPushButton('Sort on CL')
        self.sort_int_cl_btn.setEnabled(False)
        self.sort_int_cl_btn.clicked.connect(self.sort_int_on_cl)
        btn_row_layout.addWidget(self.sort_int_cl_btn)
        
        self.save_int_table_btn = QPushButton('Save to XLS')
        self.save_int_table_btn.setEnabled(False)
        self.save_int_table_btn.clicked.connect(self.save_int_table_to_excel)
        btn_row_layout.addWidget(self.save_int_table_btn)
        
        left_layout.addWidget(btn_row)
        
        layout.addWidget(left, 1)
        
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        
        controls_layout.addWidget(QLabel('X Axis:'))
        self.x_axis_int_combo = QComboBox()
        controls_layout.addWidget(self.x_axis_int_combo)
        
        controls_layout.addWidget(QLabel('Integrals:'))
        self.integrals_combo = QComboBox()
        controls_layout.addWidget(self.integrals_combo)
        
        self.draw_int_chart_btn = QPushButton('Draw Chart')
        self.draw_int_chart_btn.setEnabled(False)
        self.draw_int_chart_btn.clicked.connect(self.draw_int_chart)
        controls_layout.addWidget(self.draw_int_chart_btn)
        
        right_layout.addWidget(controls)
        
        self.int_chart_canvas = MatplotlibCanvas(widget)
        self.int_chart_toolbar = NavigationToolbar(self.int_chart_canvas, widget)
        right_layout.addWidget(self.int_chart_toolbar)
        right_layout.addWidget(self.int_chart_canvas)
        
        layout.addWidget(right, 2)
        
        return widget
    
    def _create_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')
    
    def show_documentation(self) -> None:
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        doc_path = os.path.join(base_dir, 'docs', 'manual.md')
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
            '<h3>H5 Reader</h3>'
            '<p>Version 1.0</p>'
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
            
        for group in self.current_file.groups:
            group_item = QTreeWidgetItem([group])
            self.tree_widget.addTopLevelItem(group_item)
            
            if group in self.current_file.datasets:
                for dataset in self.current_file.datasets[group]:
                    dataset_item = QTreeWidgetItem([dataset])
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
                self.plot_all_cycles(group, dataset)
            elif self.tab_widget.currentIndex() == 1:
                if (group, dataset) not in self.last_cycle_selected_items:
                    if len(self.last_cycle_selected_items) < 7:
                        self.last_cycle_selected_items.append((group, dataset))
                        self.last_cycle_selected_list.addItem(f"{group}/{dataset}")
                self.add_lines_btn.setEnabled(len(self.last_cycle_selected_items) > 0)
                self.total_clear_btn.setEnabled(len(self.last_cycle_selected_items) > 0)
                self.clear_selection_btn.setEnabled(len(self.last_cycle_selected_items) > 0)
    
    def plot_all_cycles(self, group: str, dataset: str) -> None:
        if group in ['variables', 'currents', 'forces']:
            time = self.h5_reader.read_dataset('time', '')
            data = self.h5_reader.read_dataset(group, dataset)
            
            if time is not None and data is not None:
                if self.single_mode_btn.isChecked():
                    self.all_cycles_canvas.axes.clear()
                    self.current_plot_data = {}
                
                filename = self.current_file.filename if self.current_file else 'unknown'
                self.all_cycles_canvas.axes.plot(
                    time, data, 
                    label=f'{dataset} from {filename}'
                )
                
                self.current_plot_data = {'time': time, 'data': data}
                
                self.all_cycles_canvas.axes.set_xlabel('msec')
                self.all_cycles_canvas.axes.set_title(dataset)
                self.all_cycles_canvas.axes.legend()
                
                if len(time) > 0:
                    self.up_slider.setMaximum(int(np.max(time)))
                    self.down_slider.setMaximum(int(np.max(time)))
                    self.up_slider.setValue(0)
                    self.down_slider.setValue(int(np.max(time)))
                    self.up_slider_value.setText('0')
                    self.down_slider_value.setText(str(int(np.max(time))))
                
                self.all_cycles_canvas.draw()
    
    def plot_last_cycle(self, group: str, dataset: str) -> None:
        if not self.current_file:
            return
            
        time = self.h5_reader.read_dataset('time', '')
        cycle = self.current_file.cycle
        points_mod = self.current_file.points_mod
        
        if time is not None and cycle is not None:
            t_start = int(np.max(time) + 1 - cycle - points_mod)
            t_end = int(np.max(time) + 1 - points_mod)
            
            data = self.h5_reader.read_dataset(group, dataset)
            
            if data is not None:
                min_len = min(len(time), len(data))
                t = time[t_start:t_start+min_len]
                data_cycle = data[t_start:t_start+min_len]
                t_shift = t - t[0]
                
                self.last_cycle_canvas.axes.plot(t_shift, data_cycle)
                self.last_cycle_canvas.axes.set_xlabel('msec')
                self.last_cycle_canvas.axes.set_title(dataset)
                self.last_cycle_canvas.draw()
    
    def set_single_mode(self) -> None:
        self.single_mode_btn.setChecked(True)
        self.multiple_mode_btn.setChecked(False)
    
    def set_multiple_mode(self) -> None:
        self.single_mode_btn.setChecked(False)
        self.multiple_mode_btn.setChecked(True)
    
    def toggle_stimuli(self) -> None:
        if not self.current_file or not self.current_plot_data:
            return
        
        time_data = self.current_plot_data.get('time')
        data_data = self.current_plot_data.get('data')
        
        if time_data is None or data_data is None:
            return
        
        cycle = self.current_file.cycle
        start_stim = self.current_file.start_stim if self.current_file.start_stim else 10
        
        if cycle is None:
            return
        
        h_stimuli = None
        for artist in self.all_cycles_canvas.axes.get_children():
            if hasattr(artist, 'get_label') and artist.get_label() == 'Stimuli':
                h_stimuli = artist
                break
        
        if self.show_stimuli_check.isChecked():
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
                    self.all_cycles_canvas.axes.plot(
                        x_vals, y_vals, '^r', markersize=8, 
                        markerfacecolor='r', label='Stimuli'
                    )
                    self.all_cycles_canvas.draw()
        else:
            if h_stimuli:
                h_stimuli.remove()
                self.all_cycles_canvas.draw()
    
    def clear_all_cycles_chart(self) -> None:
        self.all_cycles_canvas.axes.clear()
        self.current_plot_data = {}
        self.all_cycles_canvas.draw()
    
    def update_x_range(self) -> None:
        if not self.current_plot_data:
            return
        
        up_val = self.up_slider.value()
        down_val = self.down_slider.value()
        
        self.up_slider_value.setText(str(up_val))
        self.down_slider_value.setText(str(down_val))
        
        up_val, down_val = min(up_val, down_val), max(up_val, down_val)
        
        self.all_cycles_canvas.axes.set_xlim(up_val, down_val)
        self.all_cycles_canvas.draw()
    
    def clear_last_cycle(self) -> None:
        self.last_cycle_canvas.axes.clear()
        self.last_cycle_plots = []
        self.last_cycle_selected_items = []
        self.last_cycle_ylims = [float('inf'), float('-inf')]
        self.last_cycle_xlims = [0, 0]
        self.add_lines_btn.setEnabled(False)
        self.total_clear_btn.setEnabled(False)
        self.last_cycle_canvas.draw()
        self.last_cycle_selected_list.clear()
        self.remove_selected_btn.setEnabled(False)
        self.clear_selection_btn.setEnabled(False)
    
    def remove_selected_item(self) -> None:
        current_row = self.last_cycle_selected_list.currentRow()
        if current_row >= 0:
            self.last_cycle_selected_items.pop(current_row)
            self.last_cycle_selected_list.takeItem(current_row)
            self.add_lines_btn.setEnabled(len(self.last_cycle_selected_items) > 0)
            self.remove_selected_btn.setEnabled(self.last_cycle_selected_list.currentRow() >= 0)
    
    def clear_selection(self) -> None:
        self.last_cycle_selected_items = []
        self.last_cycle_selected_list.clear()
        self.add_lines_btn.setEnabled(False)
        self.remove_selected_btn.setEnabled(False)
        self.clear_selection_btn.setEnabled(False)
    
    def add_lines(self) -> None:
        if not self.current_file or not self.last_cycle_selected_items:
            return
        
        time = self.h5_reader.read_dataset('time', '')
        cycle = self.current_file.cycle
        points_mod = self.current_file.points_mod
        
        if time is None or cycle is None:
            return
        
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink']
        
        self.last_cycle_canvas.axes.clear()
        self.last_cycle_plots = []
        self.last_cycle_ylims = [float('inf'), float('-inf')]
        
        for idx, (group, dataset) in enumerate(self.last_cycle_selected_items):
            data = self.h5_reader.read_dataset(group, dataset)
            
            if data is not None:
                t_start = int(np.max(time) + 1 - cycle - points_mod)
                t_end = int(np.max(time) + 1 - points_mod)
                
                min_len = min(len(time), len(data), t_end + 1)
                t = time[t_start:t_start + min_len]
                data_cycle = data[t_start:t_start + min_len]
                t_shift = t - t[0]
                
                color = colors[idx % len(colors)]
                line, = self.last_cycle_canvas.axes.plot(
                    t_shift, data_cycle, color=color, label=dataset
                )
                self.last_cycle_plots.append(line)
                
                if np.min(data_cycle) < self.last_cycle_ylims[0]:
                    self.last_cycle_ylims[0] = np.min(data_cycle)
                if np.max(data_cycle) > self.last_cycle_ylims[1]:
                    self.last_cycle_ylims[1] = np.max(data_cycle)
                
                if self.last_cycle_xlims[1] == 0 or np.max(t_shift) > self.last_cycle_xlims[1]:
                    self.last_cycle_xlims = [0, np.max(t_shift)]
        
        if self.last_cycle_plots:
            self.last_cycle_canvas.axes.set_ylim(
                self.last_cycle_ylims[0] - 0.1 * abs(self.last_cycle_ylims[0]),
                self.last_cycle_ylims[1] + 0.1 * abs(self.last_cycle_ylims[1])
            )
            self.last_cycle_canvas.axes.set_xlim(self.last_cycle_xlims[0], self.last_cycle_xlims[1])
            self.last_cycle_canvas.axes.set_xlabel('msec')
            self.last_cycle_canvas.axes.legend()
        self.last_cycle_canvas.draw()
    
    def add_dep_data(self) -> None:
        if not self.current_file:
            QMessageBox.warning(self, 'Warning', 'No file selected')
            return
        
        fname = self.current_file.filename
        time = self.h5_reader.read_dataset('time', '')
        cycle = self.current_file.cycle
        points_mod = self.current_file.points_mod
        Herz = self.current_file.Herz
        
        if fname in self.dep_files:
            QMessageBox.warning(self, 'Existing Data', 'Data is already in the table')
            return
        
        if not self.dep_characteristics:
            self.dep_characteristics = [
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
                values['FXSE_D50 (ms)'] = 0
                values['FXSE_D70 (ms)'] = 0
                values['FXSE_D90 (ms)'] = 0
                values['DF_max (AFU/ms)'] = 0
                values['DF_max(norm) (1/ms)'] = 0
                values['DF_min (AFU/ms)'] = 0
                values['DF_min(norm) (1/ms)'] = 0
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

        self.dep_files.append(fname)
        self.dep_data[fname] = values
        
        self.update_dep_table()
        
        self.sort_dep_hz_btn.setEnabled(True)
        self.sort_dep_cl_btn.setEnabled(True)
        self.save_dep_table_btn.setEnabled(True)
        self.draw_dep_chart_btn.setEnabled(True)
        
        char_items = self.dep_characteristics[3:]
        self.char_dep_combo.clear()
        self.char_dep_combo.addItems(char_items)
        
        x_items = self.dep_characteristics[:2]
        self.x_axis_dep_combo.clear()
        self.x_axis_dep_combo.addItems(x_items)
        
        self.new_dep_data_btn.setText('Add data')
        
        self.status_bar.showMessage(f'Added data for: {fname}')
    
    def update_dep_table(self) -> None:
        if not self.dep_data:
            self.dep_table.setRowCount(0)
            self.dep_table.setColumnCount(0)
            return
        
        rows = len(self.dep_characteristics)
        cols = len(self.dep_files) + 1
        
        self.dep_table.setRowCount(rows)
        self.dep_table.setColumnCount(cols)
        
        self.dep_table.setHorizontalHeaderLabels(['Characteristics'] + self.dep_files)
        
        for i, char in enumerate(self.dep_characteristics):
            self.dep_table.setItem(i, 0, QTableWidgetItem(char))
            for j, fname in enumerate(self.dep_files):
                val = self.dep_data[fname].get(char, '')
                self.dep_table.setItem(i, j + 1, QTableWidgetItem(str(val)))
    
    def sort_dep_on_hz(self) -> None:
        if not self.dep_data:
            return
        
        sorted_files = sorted(self.dep_files, 
                            key=lambda f: self.dep_data[f].get('Frequency (Hz)', 0))
        self.dep_files = sorted_files
        self.update_dep_table()
        self.status_bar.showMessage('Sorted by Frequency (Hz)')
    
    def sort_dep_on_cl(self) -> None:
        if not self.dep_data:
            return
        
        sorted_files = sorted(self.dep_files, 
                            key=lambda f: self.dep_data[f].get('Cycle length (ms)', 0))
        self.dep_files = sorted_files
        self.update_dep_table()
        self.status_bar.showMessage('Sorted by Cycle length (ms)')
    
    def draw_dep_chart(self) -> None:
        x_axis = self.x_axis_dep_combo.currentText()
        char = self.char_dep_combo.currentText()
        
        if not x_axis or not char:
            return
        
        x_vals = []
        y_vals = []
        
        for fname in self.dep_files:
            x_val = self.dep_data[fname].get(x_axis, 0)
            y_val = self.dep_data[fname].get(char, 0)
            x_vals.append(x_val)
            y_vals.append(y_val)
        
        if not x_vals:
            return
        
        self.dep_chart_canvas.axes.clear()
        self.dep_chart_canvas.axes.plot(x_vals, y_vals, 'o-', markersize=8)
        self.dep_chart_canvas.axes.set_xlabel(x_axis)
        self.dep_chart_canvas.axes.set_ylabel(char)
        self.dep_chart_canvas.axes.set_title(f'{char} vs {x_axis}')
        self.dep_chart_canvas.axes.grid(True)
        self.dep_chart_canvas.draw()
        
        self.status_bar.showMessage(f'Chart: {char} vs {x_axis}')
    
    def save_dep_table_to_excel(self) -> None:
        if not self.dep_data:
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save Dependencies to Excel', '', 'Excel Files (*.xlsx)'
        )
        
        if not filepath:
            return
        
        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'
        
        import pandas as pd
        
        columns = ['Characteristics'] + self.dep_files
        data = []
        for char in self.dep_characteristics:
            row = [char]
            for fname in self.dep_files:
                row.append(self.dep_data[fname].get(char, ''))
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
        
        if fname in self.int_files:
            QMessageBox.warning(self, 'Existing Data', 'Data is already in the table')
            return
        
        if not self.int_characteristics:
            self.int_characteristics = [
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
            VnSR = float(self.current_file.fid['/parameters/V_nSR'][()]) if '/parameters/V_nSR' in self.current_file.fid else 0.005
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
            for char in self.int_characteristics[2:]:
                if char not in values:
                    values[char] = 0
        
        for char in self.int_characteristics:
            if char not in values:
                values[char] = 0
        
        self.int_files.append(fname)
        self.int_data[fname] = values
        
        self.update_int_table()
        
        self.sort_int_hz_btn.setEnabled(True)
        self.sort_int_cl_btn.setEnabled(True)
        self.save_int_table_btn.setEnabled(True)
        self.draw_int_chart_btn.setEnabled(True)
        
        self.new_int_data_btn.setText('Add data')
        
        int_items = self.int_characteristics[2:]
        self.integrals_combo.clear()
        self.integrals_combo.addItems(int_items)
        
        x_items = self.int_characteristics[:2]
        self.x_axis_int_combo.clear()
        self.x_axis_int_combo.addItems(x_items)
        
        self.status_bar.showMessage(f'Added integrals for: {fname}')
    
    def update_int_table(self) -> None:
        if not self.int_data:
            self.int_table.setRowCount(0)
            self.int_table.setColumnCount(0)
            return
        
        rows = len(self.int_characteristics)
        cols = len(self.int_files) + 1
        
        self.int_table.setRowCount(rows)
        self.int_table.setColumnCount(cols)
        
        self.int_table.setHorizontalHeaderLabels(['Integrals'] + self.int_files)
        
        for i, char in enumerate(self.int_characteristics):
            self.int_table.setItem(i, 0, QTableWidgetItem(char))
            for j, fname in enumerate(self.int_files):
                val = self.int_data[fname].get(char, '')
                self.int_table.setItem(i, j + 1, QTableWidgetItem(str(val)))
    
    def sort_int_on_hz(self) -> None:
        if not self.int_data:
            return
        
        sorted_files = sorted(self.int_files, 
                            key=lambda f: self.int_data[f].get('Frequency (Hz)', 0))
        self.int_files = sorted_files
        self.update_int_table()
        self.status_bar.showMessage('Sorted by Frequency (Hz)')
    
    def sort_int_on_cl(self) -> None:
        if not self.int_data:
            return
        
        sorted_files = sorted(self.int_files, 
                            key=lambda f: self.int_data[f].get('Cycle length (ms)', 0))
        self.int_files = sorted_files
        self.update_int_table()
        self.status_bar.showMessage('Sorted by Cycle length (ms)')
    
    def draw_int_chart(self) -> None:
        x_axis = self.x_axis_int_combo.currentText()
        char = self.integrals_combo.currentText()
        
        if not x_axis or not char:
            return
        
        x_vals = []
        y_vals = []
        
        for fname in self.int_files:
            x_val = self.int_data[fname].get(x_axis, 0)
            y_val = self.int_data[fname].get(char, 0)
            x_vals.append(x_val)
            y_vals.append(y_val)
        
        if not x_vals:
            return
        
        self.int_chart_canvas.axes.clear()
        self.int_chart_canvas.axes.plot(x_vals, y_vals, 'o-', markersize=8)
        self.int_chart_canvas.axes.set_xlabel(x_axis)
        self.int_chart_canvas.axes.set_ylabel(char)
        self.int_chart_canvas.axes.set_title(f'{char} vs {x_axis}')
        self.int_chart_canvas.axes.grid(True)
        self.int_chart_canvas.draw()
        
        self.status_bar.showMessage(f'Chart: {char} vs {x_axis}')
    
    def save_int_table_to_excel(self) -> None:
        if not self.int_data:
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save Integrals to Excel', '', 'Excel Files (*.xlsx)'
        )
        
        if not filepath:
            return
        
        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'
        
        import pandas as pd
        
        columns = ['Integrals'] + self.int_files
        data = []
        for char in self.int_characteristics:
            row = [char]
            for fname in self.int_files:
                row.append(self.int_data[fname].get(char, ''))
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


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())