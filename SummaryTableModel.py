from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QColor


class SummaryTableModel(QAbstractTableModel):
    def __init__(self, data, header, column_alignments, table_type, config_data, vertical_header=None):
        super().__init__()
        self._data = data
        self._table_type = table_type
        self.data_rows = len(self._data)
        self.data_cols = len(self._data[0]) if self._data else 0
        self._header = header if header else ['#'] * self.data_cols
        self.column_alignments = column_alignments
        self._vertical_header = vertical_header if vertical_header else [''] * self.data_rows
        self._initialize_color_maps(config_data)

        if table_type == 'overall_summary':
            self.plus_minus_index = header.index('+-')
            self.nos_index = header.index('#')

    def _initialize_color_maps(self, config_data):
        color_maps = [
            "header_color_map",
            "plus_minus_color_map",
            "text_color_map",
            "month_color_map"
        ]
        for color_map_name in color_maps:
            color_map = config_data.get(color_map_name)
            if color_map:
                for key, color in color_map.items():
                    color_map[key] = QColor(color)
                setattr(self, color_map_name, color_map)

        self.colors = {
            'bisque': QColor('#ffedd8'),
            'next_blue': QColor('#0000FF'),
            'redwood': QColor('#AB4E52')
        }


    def rowCount(self, parent=QModelIndex()):
        return self.data_rows

    def columnCount(self, parent=QModelIndex()):
        return self.data_cols

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        row, col = index.row(), index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data[row][col]
            return str(value)

        if role == Qt.TextAlignmentRole:
            return self.column_alignments.get(col, Qt.AlignRight | Qt.AlignVCenter)

        if role == Qt.BackgroundRole:
            vh = self._vertical_header[row]
            if self._table_type == "calendar" and vh in self.month_color_map:
                    return self.month_color_map[vh]
            if vh in self.text_color_map:
                return self.text_color_map[vh]
            ch = self._header[col]
            if ch in self.header_color_map:
                return self.header_color_map[ch]
            if '+-' in ch:
                i = self._data[row][self.plus_minus_index]
                return self.plus_minus_color_map[i]
            for text, color in self.text_color_map.items():
                if text in str(self._data[row][0]) or text in str(self._data[row][1]):
                    return color
            return None

        if role == Qt.ForegroundRole:
            if self._table_type == 'overall_summary' and str(self._data[row][self.nos_index]) == "0":
                return self.colors['redwood']
            if self._table_type == "calendar_details":
                if "Next" in str(self._data[row][1]):
                    return self.colors['next_blue']
                if "sell" in str(self._data[row][2]):
                    return self.colors['redwood']
            if self._table_type == "dividend_summary" and "Next" in str(self._data[row][1]):
                return self.colors['next_blue']
            if self._table_type == 'transaction_summary' and "sell" in str(self._data[row][2]):
                return self.colors['redwood']

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._header[section] if section < len(self._header) else '#'
        if orientation == Qt.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return self._vertical_header[section] if 0 <= section < len(self._vertical_header) else 'x'
