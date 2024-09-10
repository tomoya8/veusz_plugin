#  Copyright (c) 2024. by T. Konishi
#  All rights reserved.

from veusz.plugins import *
import veusz.qtall as qt
import re
import sys


class PeakDatasetPickerLog(ToolsPlugin):
    """Create dataset from a data picker console log."""

    menu = ("Peak Data from Picker Log",)
    name = "PeakDataPicker"
    description_short = 'Create peak dataset from data picker log.'
    description_full = ('Create peak dataset from data picker log stored in clipboard.\n'
                        'Check "Preferences... > Picker > Copy picked points to clipboard"\n')

    def __init__(self):
        self.fields = [
            # Intentionally not using FieldDataset here. FieldDataset sometimes fails
            field.FieldText('ds_out', 'Output dataset name', ''),
        ]

    def apply(self, interface, fields):
        ds_out_name = fields['ds_out']
        if ds_out_name == '':
            raise DatasetPluginException('Output dataset name is empty.')

        text = qt.QApplication.clipboard().text().rstrip('\n')
        if text == '':
            raise DatasetPluginException('No data found in clipboard.')

        pattern = re.compile(r'^.*?\[(\d+)\]\s=\s(\d+(\.\d+)?),\s(.*?)\[(\d+)\]\s=\s(\d+(\.\d+)?)')

        o_value = (0, 0, 0)
        p_data = []

        for line in text.split('\n'):
            match = pattern.search(line)
            if match:
                try:
                    index = int(match.group(1))
                    x_value = float(match.group(2))
                    y_value = float(match.group(6))
                    y_name = match.group(4)

                    old_index = o_value[0]
                    if abs(index - old_index) > 10:
                        if old_index == 0:
                            p_data.clear()
                        # check if the index is in the list
                        elif all(t[0] != old_index for t in p_data):
                            p_data.append(o_value)

                    # check if the y value is a peak
                    try:
                        ds_y = interface.GetData(y_name)[0]
                        if index > 3 and y_value > ds_y[(index-1)-2] and y_value > ds_y[(index-1)+2]:
                            o_value = (index, x_value, y_value)

                    except KeyError:
                        pass

                except ValueError:
                    pass

            else:
                # if we find a line that does not match the pattern, ignore previous data
                # mark to clear the data
                o_value = (0, 0, 0)

        if o_value[0] != 0:
            p_data.append(o_value)

            interface.SetData(fields['ds_out'] + '_x', [p[1] for p in p_data])
            interface.SetData(fields['ds_out'] + '_y', [p[2] for p in p_data])

            # prepare for the next data picker log
            qt.QApplication.clipboard().setText(text + '\n>>>\n')


toolspluginregistry.append(PeakDatasetPickerLog)