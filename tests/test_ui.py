import pytest
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem
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
        assert 'H5 Reader' in main_window.windowTitle()
    
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
        assert main_window.all_cycles_tab.canvas is not None
        assert main_window.all_cycles_tab.canvas.fig is not None
        assert main_window.all_cycles_tab.canvas.axes is not None
    
    def test_last_cycle_canvas_exists(self, main_window):
        assert main_window.last_cycle_tab.canvas is not None
        assert main_window.last_cycle_tab.canvas.fig is not None
    
    def test_dependencies_tab_widgets(self, main_window):
        main_window.tab_widget.setCurrentIndex(2)
        assert main_window.dependencies_tab.table is not None
        assert main_window.dependencies_tab.canvas is not None
    
    def test_integrals_tab_widgets(self, main_window):
        main_window.tab_widget.setCurrentIndex(3)
        assert main_window.integrals_tab.table is not None
        assert main_window.integrals_tab.canvas is not None
    
    def test_sliders_initial_state(self, main_window):
        main_window.tab_widget.setCurrentIndex(0)
        assert main_window.all_cycles_tab.up_slider.value() == 0
        assert main_window.all_cycles_tab.down_slider.value() == 100
    
    def test_last_cycle_selection_empty(self, main_window):
        assert len(main_window.last_cycle_tab.selected_items) == 0
        assert main_window.last_cycle_tab.plot_btn.isEnabled() == False
        assert main_window.last_cycle_tab.total_clear_btn.isEnabled() == False
    
    def test_dependencies_initial_state(self, main_window):
        assert len(main_window.dependencies_tab.data) == 0
        assert main_window.dependencies_tab.sort_hz_btn.isEnabled() == False
        assert main_window.dependencies_tab.sort_cl_btn.isEnabled() == False
        assert main_window.dependencies_tab.draw_chart_btn.isEnabled() == False
    
    def test_integrals_initial_state(self, main_window):
        assert len(main_window.integrals_tab.data) == 0
        assert main_window.integrals_tab.sort_hz_btn.isEnabled() == False
        assert main_window.integrals_tab.sort_cl_btn.isEnabled() == False
        assert main_window.integrals_tab.draw_chart_btn.isEnabled() == False


class TestMatplotlibCanvas:
    def test_canvas_creation(self, qapp):
        from src.ui.tabs import MatplotlibCanvas
        canvas = MatplotlibCanvas()
        assert canvas.fig is not None
        assert canvas.axes is not None
    
    def test_canvas_with_parent(self, qapp):
        from src.ui.tabs import MatplotlibCanvas
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        canvas = MatplotlibCanvas(parent, width=8, height=6, dpi=150)
        assert canvas.fig is not None


class TestMainWindowIntegration:
    def test_tab_switching(self, main_window):
        for i in range(main_window.tab_widget.count()):
            main_window.tab_widget.setCurrentIndex(i)
            assert main_window.tab_widget.currentIndex() == i
    
    def test_single_mode_button(self, main_window):
        main_window.all_cycles_tab.single_mode_btn.click()
        assert main_window.all_cycles_tab.single_mode_btn.isChecked() == True
        assert main_window.all_cycles_tab.multiple_mode_btn.isChecked() == False
    
    def test_multiple_mode_button(self, main_window):
        main_window.all_cycles_tab.multiple_mode_btn.click()
        assert main_window.all_cycles_tab.multiple_mode_btn.isChecked() == True
        assert main_window.all_cycles_tab.single_mode_btn.isChecked() == False
    
    def test_mode_mutual_exclusion(self, main_window):
        main_window.all_cycles_tab.single_mode_btn.click()
        assert main_window.all_cycles_tab.single_mode_btn.isChecked() == True
        main_window.all_cycles_tab.multiple_mode_btn.click()
        assert main_window.all_cycles_tab.multiple_mode_btn.isChecked() == True
        assert main_window.all_cycles_tab.single_mode_btn.isChecked() == False
    
    def test_show_stimuli_toggle(self, main_window):
        main_window.all_cycles_tab.show_stimuli_check.click()
        assert main_window.all_cycles_tab.show_stimuli_check.isChecked() == True
    
    def test_clear_chart_button_exists(self, main_window):
        assert main_window.all_cycles_tab.clear_chart_btn is not None
        assert main_window.all_cycles_tab.clear_chart_btn.text() == 'Clear Chart'
    
    def test_slider_values(self, main_window):
        main_window.all_cycles_tab.up_slider.setValue(50)
        main_window.all_cycles_tab.down_slider.setValue(80)
        assert main_window.all_cycles_tab.up_slider.value() == 50
        assert main_window.all_cycles_tab.down_slider.value() == 80
    
    def test_slider_range(self, main_window):
        assert main_window.all_cycles_tab.up_slider.minimum() == 0
        assert main_window.all_cycles_tab.up_slider.maximum() == 100
        assert main_window.all_cycles_tab.down_slider.minimum() == 0
        assert main_window.all_cycles_tab.down_slider.maximum() == 100
    
    def test_comboboxes_exist(self, main_window):
        main_window.tab_widget.setCurrentIndex(2)
        assert main_window.dependencies_tab.x_axis_combo is not None
        assert main_window.dependencies_tab.char_combo is not None
        main_window.tab_widget.setCurrentIndex(3)
        assert main_window.integrals_tab.x_axis_combo is not None
        assert main_window.integrals_tab.integrals_combo is not None
    
    def test_tree_widget_columns(self, main_window):
        assert main_window.tree_widget.columnCount() == 1
    
    def test_files_list_initially_empty(self, main_window):
        assert main_window.files_list.count() == 0
    
    def test_delete_button_initially_disabled(self, main_window):
        assert main_window.delete_file_btn.isEnabled() == False
    
    def test_status_bar_exists(self, main_window):
        assert main_window.status_bar is not None
    
    def test_menu_bar_exists(self, main_window):
        menubar = main_window.menuBar()
        assert menubar is not None
        assert menubar.actions() is not None


class TestMainWindowWithFile:
    @pytest.fixture
    def test_file(self):
        return '/home/akursanov/OpenCodeProjects/H5reader/results_1Hz_100.h5'
    
    @pytest.fixture
    def test_file2(self):
        return '/home/akursanov/OpenCodeProjects/H5reader/results_2Hz_100.h5'
    
    def test_load_real_file(self, main_window, test_file):
        initial_count = len(main_window.files)
        main_window.load_file(test_file)
        assert len(main_window.files) == initial_count + 1
        assert main_window.current_file is not None
    
    def test_plot_with_file(self, main_window, test_file):
        main_window.load_file(test_file)
        main_window.all_cycles_tab.plot('variables', 'V')
        assert len(main_window.all_cycles_tab.canvas.axes.lines) > 0
    
    def test_delete_file_enables_button(self, main_window, test_file, qtbot):
        main_window.load_file(test_file)
        main_window.files_list.setCurrentRow(0)
        main_window.on_file_selected(main_window.files_list.item(0))
        assert main_window.delete_file_btn.isEnabled() == True
    
    def test_tree_updates_after_load(self, main_window, test_file):
        main_window.load_file(test_file)
        assert main_window.tree_widget.topLevelItemCount() > 0
    
    def test_multiple_files_loaded(self, main_window, test_file, test_file2):
        main_window.load_file(test_file)
        main_window.load_file(test_file2)
        assert len(main_window.files) == 2
    
    def test_switch_between_files(self, main_window, test_file, test_file2):
        main_window.load_file(test_file)
        main_window.load_file(test_file2)
        main_window.files_list.setCurrentRow(0)
        main_window.on_file_selected(main_window.files_list.item(0))
        first_file = main_window.current_file.filename
        main_window.files_list.setCurrentRow(1)
        main_window.on_file_selected(main_window.files_list.item(1))
        assert main_window.current_file.filename != first_file


class TestIntegralsTab:
    @pytest.fixture
    def test_file(self):
        return '/home/akursanov/OpenCodeProjects/H5reader/results_1Hz_100.h5'
    
    def test_integrals_tab_widgets_exist(self, main_window):
        main_window.tab_widget.setCurrentIndex(3)
        assert main_window.integrals_tab.table is not None
        assert main_window.integrals_tab.canvas is not None
        assert main_window.integrals_tab.toolbar is not None
    
    def test_integrals_buttons_initially_disabled(self, main_window):
        main_window.tab_widget.setCurrentIndex(3)
        assert main_window.integrals_tab.sort_hz_btn.isEnabled() == False
        assert main_window.integrals_tab.sort_cl_btn.isEnabled() == False
        assert main_window.integrals_tab.save_btn.isEnabled() == False
        assert main_window.integrals_tab.draw_chart_btn.isEnabled() == False
    
    def test_integrals_new_data_button_exists(self, main_window):
        main_window.tab_widget.setCurrentIndex(3)
        assert main_window.integrals_tab.new_data_btn is not None
        assert main_window.integrals_tab.new_data_btn.text() in ['New Data', 'Add data']
    
    def test_integrals_combos_exist(self, main_window):
        main_window.tab_widget.setCurrentIndex(3)
        assert main_window.integrals_tab.x_axis_combo is not None
        assert main_window.integrals_tab.integrals_combo is not None


class TestDependenciesTab:
    @pytest.fixture
    def test_file(self):
        return '/home/akursanov/OpenCodeProjects/H5reader/results_1Hz_100.h5'
    
    def test_dependencies_tab_widgets_exist(self, main_window):
        main_window.tab_widget.setCurrentIndex(2)
        assert main_window.dependencies_tab.table is not None
        assert main_window.dependencies_tab.canvas is not None
        assert main_window.dependencies_tab.toolbar is not None
    
    def test_dependencies_buttons_initially_disabled(self, main_window):
        main_window.tab_widget.setCurrentIndex(2)
        assert main_window.dependencies_tab.sort_hz_btn.isEnabled() == False
        assert main_window.dependencies_tab.sort_cl_btn.isEnabled() == False
        assert main_window.dependencies_tab.save_btn.isEnabled() == False
        assert main_window.dependencies_tab.draw_chart_btn.isEnabled() == False
    
    def test_dependencies_combos_exist(self, main_window):
        main_window.tab_widget.setCurrentIndex(2)
        assert main_window.dependencies_tab.x_axis_combo is not None
        assert main_window.dependencies_tab.char_combo is not None


class TestEdgeCases:
    def test_plot_without_file_creates_empty_plot(self, main_window):
        main_window.all_cycles_tab.plot('variables', 'V')
        assert len(main_window.all_cycles_tab.canvas.axes.lines) == 0
    
    def test_delete_file_empty_list_no_error(self, main_window):
        main_window.delete_file()
        assert main_window.files == []
    
    def test_add_lines_no_selection(self, main_window):
        main_window.last_cycle_tab.plot()
        assert main_window.last_cycle_tab.selected_items == []
    
    def test_clear_chart_empty_plot(self, main_window):
        main_window.all_cycles_tab.clear_chart()
        assert len(main_window.all_cycles_tab.canvas.axes.lines) == 0
    
    def test_update_x_range_no_data(self, main_window):
        main_window.all_cycles_tab.update_x_range()
        assert main_window.all_cycles_tab.up_slider.value() == 0
    
    def test_clear_selection_empty(self, main_window):
        main_window.last_cycle_tab.clear_selection()
        assert main_window.last_cycle_tab.selected_items == []


class TestLastCycleTab:
    @pytest.fixture
    def test_file(self):
        return '/home/akursanov/OpenCodeProjects/H5reader/results_1Hz_100.h5'
    
    def test_last_cycle_tab_widgets_exist(self, main_window):
        main_window.tab_widget.setCurrentIndex(1)
        assert main_window.last_cycle_tab.canvas is not None
        assert main_window.last_cycle_tab.toolbar is not None
        assert main_window.last_cycle_tab.selected_list is not None
    
    def test_last_cycle_buttons_exist(self, main_window):
        main_window.tab_widget.setCurrentIndex(1)
        assert main_window.last_cycle_tab.plot_btn is not None
        assert main_window.last_cycle_tab.remove_selected_btn is not None
        assert main_window.last_cycle_tab.clear_selection_btn is not None
        assert main_window.last_cycle_tab.total_clear_btn is not None
    
    def test_last_cycle_buttons_initially_disabled(self, main_window):
        main_window.tab_widget.setCurrentIndex(1)
        assert main_window.last_cycle_tab.plot_btn.isEnabled() == False
        assert main_window.last_cycle_tab.total_clear_btn.isEnabled() == False


class TestHelpMenu:
    def test_help_menu_exists(self, main_window):
        menubar = main_window.menuBar()
        menus = [menubar.actions()[i].text() for i in range(menubar.actions().__len__())]
        help_menu_found = any('Help' in menu for menu in menus)
        assert help_menu_found
    
    def test_show_documentation_method_exists(self, main_window):
        assert hasattr(main_window, 'show_documentation')
        assert callable(main_window.show_documentation)
    
    def test_show_about_method_exists(self, main_window):
        assert hasattr(main_window, 'show_about')
        assert callable(main_window.show_about)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
