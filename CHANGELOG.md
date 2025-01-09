# Changelog

## [Unreleased]
### Fixed
- Test suite hanging:
```python
@pytest.fixture(autouse=True)
def cleanup_windows():
    yield
    for window in QApplication.topLevelWidgets():
        window.close()
        window.deleteLater()
    QApplication.processEvents()
```

- Right-click menu in combo box:
```python
def eventFilter(self, source, event):
    if event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
        index = self.view().indexAt(event.pos())
        if index.isValid():
            text = self.itemText(index.row())
            if text and text != "Add Schedule":
                self.setCurrentIndex(index.row())
                self.context_menu.exec_(self.view().mapToGlobal(event.pos()))
                return True
    return super().eventFilter(source, event)
```

- Graph regeneration KeyError:
```python
def regenerate_graph(self):
    for cycle in self.current_schedule:
        # Changed from cycle['Duration'] to cycle['CycleTime']
        cycle_time_minutes = self.time_to_minutes(cycle['CycleTime'])
        x_data.extend([current_time, current_time + cycle_time_minutes])
```

- Message box styling:
```python
def get_message_box_style():
    theme = ThemeManager.get_current_theme()
    return f"""
        QMessageBox {{
            background-color: {theme['background']};
        }}
        QMessageBox QLabel {{
            color: {theme['text']};
        }}
    """

### Added
- Type hints:
```python
def validate_and_collect_entries(self, show_warnings: bool = True) -> Optional[List[Dict]]:
    """Validate and collect all entries from the table."""

## [1.0.0] - 2024-03-19
### Added
- Initial release 