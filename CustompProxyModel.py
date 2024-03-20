from PyQt5 import QtCore
from PyQt5.QtCore import Qt


class CustomProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, nos_index):
        super().__init__()
        self.filter_text = ""
        self.nos_index = nos_index
        self.show_closed_positions = False

    def setFilterParams(self, text, show_closed_positions=False, search_all_columns=False):
        self.filter_text = text
        self.show_closed_positions = show_closed_positions
        self.search_all_columns=search_all_columns
        self.invalidateFilter()  # Trigger filter reevaluation

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if not self.show_closed_positions:
            source_model = self.sourceModel()
            index = source_model.index(sourceRow, self.nos_index, sourceParent)
            text = source_model.data(index, Qt.DisplayRole)
            if text == '0':
                return False

        if self.filter_text:
            source_model = self.sourceModel()
            if self.search_all_columns:
                for column in range(source_model.columnCount()):
                    index = source_model.index(sourceRow, column, sourceParent)
                    data = source_model.data(index, Qt.DisplayRole)
                    if self.filter_text in data.lower():
                        return True
                return False
            else:
                index = source_model.index(sourceRow, 0, sourceParent)
                data = source_model.data(index, Qt.DisplayRole)
                if self.filter_text in data.lower():
                    return True
                return False

        return True
