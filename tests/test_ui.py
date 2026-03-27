import pytest
from PyQt6.QtWidgets import QApplication
import sys


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def main_window(qapp):
    from src.ui.main_window import MainWindow
    window = MainWindow()
    yield window
    window.close()


class TestMainWindow:
    def test_window_creation(self, main_window):
        assert main_window is not None
        assert main_window.windowTitle() == 'H5 Reader'
    
    def test_initial_state(self, main_window):
        assert main_window.current_file is None
        assert len(main_window.files) == 0
        assert main_window.tab_widget.count() == 4
    
    def test_tabs_exist(self, main_window):
        tabs = [
            main_window.tab_widget.tabText(i) 
            for i in range(main_window.tab_widget.count())
        ]
        assert 'All Cycles' in tabs
        assert 'Last Cycle' in tabs
        assert 'Dependencies' in tabs
        assert 'Integrals' in tabs
    
    def test_files_list_exists(self, main_window):
        assert main_window.files_list is not None
    
    def test_tree_widget_exists(self, main_window):
        assert main_window.tree_widget is not None
    
    def test_all_cycles_canvas_exists(self, main_window):
        assert main_window.all_cycles_canvas is not None
        assert main_window.all_cycles_canvas.fig is not None
        assert main_window.all_cycles_canvas.axes is not None
    
    def test_last_cycle_canvas_exists(self, main_window):
        assert main_window.last_cycle_canvas is not None
        assert main_window.last_cycle_canvas.fig is not None
    
    def test_dependencies_tab_widgets(self, main_window):
        main_window.tab_widget.setCurrentIndex(2)
        assert main_window.dep_table is not None
        assert main_window.dep_chart_canvas is not None
    
    def test_integrals_tab_widgets(self, main_window):
        main_window.tab_widget.setCurrentIndex(3)
        assert main_window.int_table is not None
        assert main_window.int_chart_canvas is not None
    
    def test_sliders_initial_state(self, main_window):
        main_window.tab_widget.setCurrentIndex(0)
        assert main_window.up_slider.value() == 0
        assert main_window.down_slider.value() == 100
    
    def test_last_cycle_selection_empty(self, main_window):
        assert len(main_window.last_cycle_selected_items) == 0
        assert main_window.add_lines_btn.isEnabled() == False
        assert main_window.total_clear_btn.isEnabled() == False
    
    def test_dependencies_initial_state(self, main_window):
        assert len(main_window.dep_data) == 0
        assert main_window.sort_dep_hz_btn.isEnabled() == False
        assert main_window.sort_dep_cl_btn.isEnabled() == False
        assert main_window.draw_dep_chart_btn.isEnabled() == False
    
    def test_integrals_initial_state(self, main_window):
        assert len(main_window.int_data) == 0
        assert main_window.sort_int_hz_btn.isEnabled() == False
        assert main_window.sort_int_cl_btn.isEnabled() == False
        assert main_window.draw_int_chart_btn.isEnabled() == False


class TestMatplotlibCanvas:
    def test_canvas_creation(self, qapp):
        from src.ui.main_window import MatplotlibCanvas
        canvas = MatplotlibCanvas()
        assert canvas.fig is not None
        assert canvas.axes is not None
    
    def test_canvas_with_parent(self, qapp):
        from src.ui.main_window import MatplotlibCanvas
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        canvas = MatplotlibCanvas(parent, width=8, height=6, dpi=150)
        assert canvas.fig is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
