#  Copyright (c) 2024. by T. Konishi
#  All rights reserved.

from veusz.plugins import *
import veusz.qtall as qt
import re


class PeakDatasetPickerLog(ToolsPlugin):
    """Create dataset from a data picker console log."""

    menu = ("Peak Data from Picker Log",)
    name = "PeakDataPicker"
    description_short = 'Create peak dataset from data picker log.'
    description_full = 'Create peak dataset from data picker log stored in clipboard.'

    def __init__(self):
        self.fields = [
            field.FieldDataset('ds_out', 'Output dataset name', 'marker'),
        ]

    def apply(self, interface, fields):
        text = qt.QApplication.clipboard().text().rstrip('\n')

        if text == '':
            raise DatasetPluginException('No data found in clipboard.')

        pattern = re.compile(r'^.*?\[(\d+)\]\s=\s(\d+(\.\d+)?),\s(.*?)\[(\d+)\]\s=\s(\d+(\.\d+)?)')

        old_index = old_x_value = old_y_value = 0
        i_data = []
        x_data = []
        y_data = []

        for line in text.split('\n'):
            match = pattern.search(line)
            if match:
                try:
                    index = int(match.group(1))
                    x_value = float(match.group(2))
                    y_value = float(match.group(6))
                    y_name = match.group(4)

                    if abs(index - old_index) > 10:
                        if old_index == 0:
                            i_data.clear()
                            x_data.clear()
                            y_data.clear()
                        elif old_index not in i_data:
                            i_data.append(old_index)
                            x_data.append(old_x_value)
                            y_data.append(old_y_value)

                    # check if the index is in the list
                    ds_y = interface.GetData(y_name)[0]
                    if y_value > ds_y[(index-1)-2] and y_value > ds_y[(index-1)+2]:
                        old_index = index
                        old_x_value = x_value
                        old_y_value = y_value

                except ValueError:
                    pass

            else:
                # if we find a line that does not match the pattern, ignore previous data
                # mark to clear the data
                old_index = 0

        x_data.append(old_x_value)
        y_data.append(old_y_value)

        interface.SetData(fields['ds_out'] + '_x', x_data)
        interface.SetData(fields['ds_out'] + '_y', y_data)


toolspluginregistry.append(PeakDatasetPickerLog)