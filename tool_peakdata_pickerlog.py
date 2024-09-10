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
                        'Check "Preferences... > Picker > Copy picked points to clipboard"\n'
                        'Select peaks using data picker and push "Apply" button.\n'
                        'Peak data will be stored in two datasets: [name]_x and [name]_y.\n')

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
            raise DatasetPluginException('Clipboard is empty.')

        pattern = re.compile(r'^.*?\[([-\d]+)\]\s=\s([-\d]+(\.\d+)?),\s(.*?)\[([-\d]+)\]\s=\s([-\d]+(\.\d+)?)')

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

                    if o_value != (0, 0, 0) and abs(index - o_value[0]) > 10:
                        p_data.append(o_value)

                    try:
                        # check if the y value is a peak or a ditch
                        ds_y = interface.GetData(y_name)[0]
                        if index > 3 and (y_value - ds_y[(index-1)-2]) * (y_value - ds_y[(index-1)+2]) > 0:
                            o_value = (index, x_value, y_value)

                    except KeyError:
                        pass

                except ValueError:
                    pass

            else:
                # if we find a line that does not match the pattern, ignore the previous data block
                o_value = (0, 0, 0)
                p_data.clear()

        if o_value != (0, 0, 0):
            p_data.append(o_value)

            # remove duplicates and sort by index
            p_data = list(dict.fromkeys(sorted(p_data, key=lambda t: t[0])))

            interface.SetData(ds_out_name + '_x', [p[1] for p in p_data])
            interface.SetData(ds_out_name + '_y', [p[2] for p in p_data])

            # prepare for the next apply
            # intentionally adds a non-matching line to ignore the previous data block
            qt.QApplication.clipboard().setText(text + '\n>>>\n')

        else:
            raise DatasetPluginException('No peak data found in the clipboard.')


toolspluginregistry.append(PeakDatasetPickerLog)