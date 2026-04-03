"""
UI tabs module for H5 Reader application.

Contains tab widgets for displaying and analyzing HDF5 data.
"""
from typing import Optional, Dict, Any, List, Tuple, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QListWidget, QListWidgetItem, QTableWidget,
    QTableWidgetItem, QComboBox, QFrame, QSplitter
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np


class MatplotlibCanvas(FigureCanvas):
    """
    Matplotlib canvas widget for PyQt6.
    
    Provides a Figure canvas embedded in a Qt widget for plotting.
    """
    
    def __init__(self, parent: Optional[QWidget] = None, width: float = 6, height: float = 4, dpi: int = 100) -> None:
        """
        Initialize canvas.
        
        Args:
            parent: Parent widget
            width: Figure width in inches
            height: Figure height in inches
            dpi: Dots per inch resolution
        """
        self.fig: Figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)


class AllCyclesTab:
    """
    Tab widget for displaying all cycles data.
    
    Allows plotting of time-series data from all simulation cycles.
    """
    
    def __init__(self, parent: QWidget, h5_reader, get_current_file: Callable):
        """
        Initialize All Cycles tab.
        
        Args:
            parent: Parent widget
            h5_reader: H5Reader instance
            get_current_file: Callable returning current H5File
        """
        self.parent = parent
        self.h5_reader = h5_reader
        self.get_current_file = get_current_file
        self.current_plot_data: Dict[str, Any] = {}
        
        self.widget = QWidget()
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create UI components."""
        layout = QVBoxLayout(self.widget)
        
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        
        self.mode_switch_label = QLabel('Mode:')
        toolbar_layout.addWidget(self.mode_switch_label)
        
        self.single_mode_btn = QPushButton('Single')
        self.single_mode_btn.setCheckable(True)
        self.single_mode_btn.setChecked(True)
        toolbar_layout.addWidget(self.single_mode_btn)
        
        self.multiple_mode_btn = QPushButton('Multiple')
        self.multiple_mode_btn.setCheckable(True)
        toolbar_layout.addWidget(self.multiple_mode_btn)
        
        toolbar_layout.addStretch()
        
        self.show_stimuli_check = QPushButton('Show Stimuli')
        self.show_stimuli_check.setCheckable(True)
        toolbar_layout.addWidget(self.show_stimuli_check)
        
        self.clear_chart_btn = QPushButton('Clear Chart')
        toolbar_layout.addWidget(self.clear_chart_btn)
        
        layout.addWidget(toolbar)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.canvas = MatplotlibCanvas(self.widget)
        self.toolbar = NavigationToolbar(self.canvas, self.widget)
        splitter.addWidget(self.toolbar)
        splitter.addWidget(self.canvas)
        
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
        down_slider_row_layout.addWidget(self.down_slider)
        self.down_slider_value = QLabel('100')
        down_slider_row_layout.addWidget(self.down_slider_value)
        sliders_layout.addWidget(down_slider_row)
        
        splitter.addWidget(sliders_widget)
        
        layout.addWidget(splitter)
    
    def get_widget(self) -> QWidget:
        """Get the main widget."""
        return self.widget
    
    def plot(self, group: str, dataset: str) -> None:
        """
        Plot data for specified group and dataset.
        
        Args:
            group: HDF5 group name (variables, currents, forces)
            dataset: Dataset name to plot
        """
        current_file = self.get_current_file()
        if not current_file:
            return
        
        if group in ['variables', 'currents', 'forces']:
            time = self.h5_reader.read_dataset('time', '')
            data = self.h5_reader.read_dataset(group, dataset)
            
            if time is not None and data is not None:
                if self.single_mode_btn.isChecked():
                    self.canvas.axes.clear()
                    self.current_plot_data = {}
                
                self.canvas.axes.plot(
                    time, data, 
                    label=f'{dataset} from {current_file.filename}'
                )
                
                self.current_plot_data = {'time': time, 'data': data}
                
                self.canvas.axes.set_xlabel('msec')
                self.canvas.axes.set_title(dataset)
                self.canvas.axes.legend()
                
                if len(time) > 0:
                    max_time = int(np.max(time))
                    self.up_slider.setMaximum(max_time)
                    self.down_slider.setMaximum(max_time)
                    self.up_slider.setValue(0)
                    self.down_slider.setValue(max_time)
                    self.up_slider_value.setText('0')
                    self.down_slider_value.setText(str(max_time))
                
                self.canvas.draw()
    
    def clear_chart(self) -> None:
        """Clear the chart."""
        self.canvas.axes.clear()
        self.current_plot_data = {}
        self.canvas.draw()
    
    def update_x_range(self) -> None:
        """Update x-axis range from slider values."""
        if not self.current_plot_data:
            return
        
        up_val = self.up_slider.value()
        down_val = self.down_slider.value()
        
        self.up_slider_value.setText(str(up_val))
        self.down_slider_value.setText(str(down_val))
        
        up_val, down_val = min(up_val, down_val), max(up_val, down_val)
        
        self.canvas.axes.set_xlim(up_val, down_val)
        self.canvas.draw()


class LastCycleTab:
    """
    Tab widget for displaying last cycle data.
    
    Allows selection and plotting of multiple datasets from the last cycle.
    """
    
    def __init__(self, parent: QWidget, h5_reader, get_current_file: Callable):
        """
        Initialize Last Cycle tab.
        
        Args:
            parent: Parent widget
            h5_reader: H5Reader instance
            get_current_file: Callable returning current H5File
        """
        self.parent = parent
        self.h5_reader = h5_reader
        self.get_current_file = get_current_file
        self.selected_items: List[Tuple[str, str]] = []
        self.plot_data: List[Tuple[str, str, str]] = []
        self.cached_data: Dict[str, Dict[str, np.ndarray]] = {}
        self.page: int = 0
        self.per_page: int = 6
        
        self.widget = QWidget()
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create UI components."""
        layout = QVBoxLayout(self.widget)
        
        layout.addWidget(QLabel('Select items in tree, then click Plot:'))
        
        self.selected_list = QListWidget()
        self.selected_list.setMaximumHeight(80)
        layout.addWidget(self.selected_list)
        
        selection_btns = QHBoxLayout()
        
        self.remove_selected_btn = QPushButton('Remove Selected')
        self.remove_selected_btn.setEnabled(False)
        selection_btns.addWidget(self.remove_selected_btn)
        
        self.clear_selection_btn = QPushButton('Clear Selection')
        self.clear_selection_btn.setEnabled(False)
        selection_btns.addWidget(self.clear_selection_btn)
        
        selection_btns.addStretch()
        layout.addLayout(selection_btns)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.canvas = MatplotlibCanvas(self.widget)
        self.toolbar = NavigationToolbar(self.canvas, self.widget)
        splitter.addWidget(self.toolbar)
        splitter.addWidget(self.canvas)
        
        layout.addWidget(splitter)
        
        btn_layout = QHBoxLayout()
        
        self.plot_btn = QPushButton('Plot')
        self.plot_btn.setEnabled(False)
        btn_layout.addWidget(self.plot_btn)
        
        self.prev_page_btn = QPushButton('<')
        self.prev_page_btn.setEnabled(False)
        btn_layout.addWidget(self.prev_page_btn)
        
        self.page_label = QLabel('1/1')
        btn_layout.addWidget(self.page_label)
        
        self.next_page_btn = QPushButton('>')
        self.next_page_btn.setEnabled(False)
        btn_layout.addWidget(self.next_page_btn)
        
        self.total_clear_btn = QPushButton('Total Clear')
        self.total_clear_btn.setEnabled(False)
        btn_layout.addWidget(self.total_clear_btn)
        
        layout.addLayout(btn_layout)
    
    def get_widget(self) -> QWidget:
        """Get the main widget."""
        return self.widget
    
    def add_selection(self, group: str, dataset: str) -> None:
        """
        Add dataset to selection.
        
        Args:
            group: HDF5 group name
            dataset: Dataset name
        """
        if (group, dataset) not in self.selected_items:
            self.selected_items.append((group, dataset))
            self.selected_list.addItem(f"{group}/{dataset}")
        self._update_buttons()
    
    def remove_selected(self) -> None:
        """Remove selected item from list."""
        current_row = self.selected_list.currentRow()
        if current_row >= 0:
            self.selected_items.pop(current_row)
            self.selected_list.takeItem(current_row)
            self._update_buttons()
    
    def clear_selection(self) -> None:
        """Clear all selections."""
        self.selected_items = []
        self.selected_list.clear()
        self._update_buttons()
    
    def _update_buttons(self) -> None:
        """Update button enabled states."""
        has_items = len(self.selected_items) > 0
        self.plot_btn.setEnabled(has_items)
        self.remove_selected_btn.setEnabled(self.selected_list.currentRow() >= 0)
        self.total_clear_btn.setEnabled(has_items)
        self.clear_selection_btn.setEnabled(has_items)
    
    def plot(self) -> None:
        """Plot selected datasets."""
        current_file = self.get_current_file()
        if not current_file or not self.selected_items:
            return
        
        time = self.h5_reader.read_dataset('time', '')
        cycle = current_file.cycle
        points_mod = current_file.points_mod
        
        if time is None or cycle is None:
            return
        
        filename = current_file.filename
        
        new_items = [(g, d, filename) for g, d in self.selected_items]
        
        for item in new_items:
            if item not in self.plot_data:
                self.plot_data.append(item)
        
        for item_group, item_dataset, item_filename in new_items:
            if item_filename not in self.cached_data:
                self.cached_data[item_filename] = {}
            
            cache_key = f"{item_group}_{item_dataset}"
            
            if cache_key not in self.cached_data[item_filename]:
                data = self.h5_reader.read_dataset(item_group, item_dataset)
                if data is not None:
                    t_start = int(np.max(time) + 1 - cycle - points_mod)
                    t_end = int(np.max(time) + 1 - points_mod)
                    min_len = min(len(time), len(data), t_end + 1)
                    data_cycle = data[t_start:t_start + min_len]
                    self.cached_data[item_filename][cache_key] = data_cycle
        
        self._redraw()
    
    def _redraw(self) -> None:
        """Redraw all plots."""
        if not self.plot_data:
            return
        
        current_file = self.get_current_file()
        if not current_file:
            return
        
        time = self.h5_reader.read_dataset('time', '')
        cycle = current_file.cycle
        points_mod = current_file.points_mod
        
        if time is None or cycle is None:
            return
        
        unique_datasets = list(set((g, d) for g, d, _ in self.plot_data))
        
        total_pages = max(1, (len(unique_datasets) + self.per_page - 1) // self.per_page)
        if self.page >= total_pages:
            self.page = total_pages - 1
        if self.page < 0:
            self.page = 0
        
        self.page_label.setText(f"{self.page + 1}/{total_pages}")
        self.prev_page_btn.setEnabled(self.page > 0)
        self.next_page_btn.setEnabled(self.page < total_pages - 1)
        
        cols = 3
        rows = 2
        
        start_idx = self.page * self.per_page
        end_idx = min(start_idx + self.per_page, len(unique_datasets))
        page_datasets = unique_datasets[start_idx:end_idx]
        
        self.canvas.fig.clear()
        
        all_filenames = list(set(f for _, _, f in self.plot_data))
        
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta',
                  'navy', 'maroon', 'olive', 'teal', 'silver', 'lime', 'aqua', 'fuchsia', 'yellow', 'black']
        
        file_colors = {fn: colors[i % len(colors)] for i, fn in enumerate(all_filenames)}
        
        lines = []
        labels = []
        
        for idx, (group, dataset) in enumerate(page_datasets):
            ax = self.canvas.fig.add_subplot(rows, cols, idx + 1)
            
            items_for_signal = [item for item in self.plot_data if item[0] == group and item[1] == dataset]
            
            for item_group, item_dataset, item_filename in items_for_signal:
                cache_key = f"{item_group}_{item_dataset}"
                data_cycle = self.cached_data.get(item_filename, {}).get(cache_key)
                
                if data_cycle is not None and len(data_cycle) > 0:
                    t_start = int(np.max(time) + 1 - cycle - points_mod)
                    min_len = min(len(time), len(data_cycle))
                    t = time[t_start:t_start + min_len]
                    t_shift = t - t[0] if len(t) > 0 else np.arange(len(data_cycle))
                    
                    color = file_colors.get(item_filename, 'blue')
                    line, = ax.plot(t_shift, data_cycle[:len(t_shift)], color=color, label=item_filename)
                    if item_filename not in labels:
                        lines.append(line)
                        labels.append(item_filename)
            
            ax.set_xlabel('msec')
            ax.set_title(f'{dataset}')
            ax.grid(True)
        
        if lines:
            self.canvas.fig.legend(lines, labels, loc='upper right', bbox_to_anchor=(0.99, 0.99))
        
        self.canvas.fig.tight_layout(rect=(0, 0, 0.95, 0.95))
        self.canvas.draw()
    
    def prev_page(self) -> None:
        """Go to previous page."""
        if self.page > 0:
            self.page -= 1
            self._redraw()
    
    def next_page(self) -> None:
        """Go to next page."""
        unique_datasets = list(set((g, d) for g, d, _ in self.plot_data))
        total_pages = max(1, (len(unique_datasets) + self.per_page - 1) // self.per_page)
        if self.page < total_pages - 1:
            self.page += 1
            self._redraw()
    
    def clear(self) -> None:
        """Clear all plots and selections."""
        self.canvas.fig.clear()
        self.canvas.axes = self.canvas.fig.add_subplot(111)
        self.plot_data = []
        self.selected_items = []
        self.cached_data = {}
        self.page = 0
        self.plot_btn.setEnabled(False)
        self.total_clear_btn.setEnabled(False)
        self.page_label.setText('1/1')
        self.prev_page_btn.setEnabled(False)
        self.next_page_btn.setEnabled(False)
        self.canvas.draw()
        self.selected_list.clear()
        self.remove_selected_btn.setEnabled(False)
        self.clear_selection_btn.setEnabled(False)


class DependenciesTab:
    """
    Tab widget for displaying dependencies between frequency and characteristics.
    
    Shows table of calculated characteristics and allows plotting dependencies.
    """
    
    def __init__(self, parent: QWidget):
        """
        Initialize Dependencies tab.
        
        Args:
            parent: Parent widget
        """
        self.widget = QWidget()
        self.data: Dict[str, Dict[str, float]] = {}
        self.files: List[str] = []
        self.characteristics: List[str] = []
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create UI components."""
        layout = QHBoxLayout(self.widget)
        
        left = QWidget()
        left_layout = QVBoxLayout(left)
        
        left_layout.addWidget(QLabel('Data Table:'))
        
        self.table = QTableWidget()
        left_layout.addWidget(self.table)
        
        btn_row = QWidget()
        btn_row_layout = QHBoxLayout(btn_row)
        
        self.new_data_btn = QPushButton('New Data')
        btn_row_layout.addWidget(self.new_data_btn)
        
        self.sort_hz_btn = QPushButton('Sort on Hz')
        self.sort_hz_btn.setEnabled(False)
        btn_row_layout.addWidget(self.sort_hz_btn)
        
        self.sort_cl_btn = QPushButton('Sort on CL')
        self.sort_cl_btn.setEnabled(False)
        btn_row_layout.addWidget(self.sort_cl_btn)
        
        self.save_btn = QPushButton('Save to XLS')
        self.save_btn.setEnabled(False)
        btn_row_layout.addWidget(self.save_btn)
        
        left_layout.addWidget(btn_row)
        
        layout.addWidget(left, 1)
        
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        
        controls_layout.addWidget(QLabel('X Axis:'))
        self.x_axis_combo = QComboBox()
        controls_layout.addWidget(self.x_axis_combo)
        
        controls_layout.addWidget(QLabel('Characteristics:'))
        self.char_combo = QComboBox()
        controls_layout.addWidget(self.char_combo)
        
        self.draw_chart_btn = QPushButton('Draw Chart')
        self.draw_chart_btn.setEnabled(False)
        controls_layout.addWidget(self.draw_chart_btn)
        
        right_layout.addWidget(controls)
        
        self.canvas = MatplotlibCanvas(self.widget)
        self.toolbar = NavigationToolbar(self.canvas, self.widget)
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        
        layout.addWidget(right, 2)
    
    def get_widget(self) -> QWidget:
        """Get the main widget."""
        return self.widget
    
    def update_table(self) -> None:
        """Update the data table."""
        if not self.data:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return
        
        rows = len(self.characteristics)
        cols = len(self.files) + 1
        
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)
        
        self.table.setHorizontalHeaderLabels(['Characteristics'] + self.files)
        
        for i, char in enumerate(self.characteristics):
            self.table.setItem(i, 0, QTableWidgetItem(char))
            for j, fname in enumerate(self.files):
                val = self.data[fname].get(char, '')
                self.table.setItem(i, j + 1, QTableWidgetItem(str(val)))
    
    def enable_controls(self) -> None:
        """Enable controls after data is added."""
        self.sort_hz_btn.setEnabled(True)
        self.sort_cl_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.draw_chart_btn.setEnabled(True)
        
        char_items = self.characteristics[3:]
        self.char_combo.clear()
        self.char_combo.addItems(char_items)
        
        x_items = self.characteristics[:2]
        self.x_axis_combo.clear()
        self.x_axis_combo.addItems(x_items)
        
        self.new_data_btn.setText('Add data')


class IntegralsTab:
    """
    Tab widget for displaying calcium integrals.
    
    Shows table of calculated integrals and allows plotting.
    """
    
    def __init__(self, parent: QWidget):
        """
        Initialize Integrals tab.
        
        Args:
            parent: Parent widget
        """
        self.widget = QWidget()
        self.data: Dict[str, Dict[str, float]] = {}
        self.files: List[str] = []
        self.characteristics: List[str] = []
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create UI components."""
        layout = QHBoxLayout(self.widget)
        
        left = QWidget()
        left_layout = QVBoxLayout(left)
        
        left_layout.addWidget(QLabel('Integrals Table:'))
        
        self.table = QTableWidget()
        left_layout.addWidget(self.table)
        
        btn_row = QWidget()
        btn_row_layout = QHBoxLayout(btn_row)
        
        self.new_data_btn = QPushButton('New Data')
        btn_row_layout.addWidget(self.new_data_btn)
        
        self.sort_hz_btn = QPushButton('Sort on Hz')
        self.sort_hz_btn.setEnabled(False)
        btn_row_layout.addWidget(self.sort_hz_btn)
        
        self.sort_cl_btn = QPushButton('Sort on CL')
        self.sort_cl_btn.setEnabled(False)
        btn_row_layout.addWidget(self.sort_cl_btn)
        
        self.save_btn = QPushButton('Save to XLS')
        self.save_btn.setEnabled(False)
        btn_row_layout.addWidget(self.save_btn)
        
        left_layout.addWidget(btn_row)
        
        layout.addWidget(left, 1)
        
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        
        controls_layout.addWidget(QLabel('X Axis:'))
        self.x_axis_combo = QComboBox()
        controls_layout.addWidget(self.x_axis_combo)
        
        controls_layout.addWidget(QLabel('Integrals:'))
        self.integrals_combo = QComboBox()
        controls_layout.addWidget(self.integrals_combo)
        
        self.draw_chart_btn = QPushButton('Draw Chart')
        self.draw_chart_btn.setEnabled(False)
        controls_layout.addWidget(self.draw_chart_btn)
        
        right_layout.addWidget(controls)
        
        self.canvas = MatplotlibCanvas(self.widget)
        self.toolbar = NavigationToolbar(self.canvas, self.widget)
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        
        layout.addWidget(right, 2)
    
    def get_widget(self) -> QWidget:
        """Get the main widget."""
        return self.widget
    
    def update_table(self) -> None:
        """Update the data table."""
        if not self.data:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return
        
        rows = len(self.characteristics)
        cols = len(self.files) + 1
        
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)
        
        self.table.setHorizontalHeaderLabels(['Integrals'] + self.files)
        
        for i, char in enumerate(self.characteristics):
            self.table.setItem(i, 0, QTableWidgetItem(char))
            for j, fname in enumerate(self.files):
                val = self.data[fname].get(char, '')
                self.table.setItem(i, j + 1, QTableWidgetItem(str(val)))
    
    def enable_controls(self) -> None:
        """Enable controls after data is added."""
        self.sort_hz_btn.setEnabled(True)
        self.sort_cl_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.draw_chart_btn.setEnabled(True)
        
        int_items = self.characteristics[2:]
        self.integrals_combo.clear()
        self.integrals_combo.addItems(int_items)
        
        x_items = self.characteristics[:2]
        self.x_axis_combo.clear()
        self.x_axis_combo.addItems(x_items)
        
        self.new_data_btn.setText('Add data')
