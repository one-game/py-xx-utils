# -*- coding: utf-8 -*-

# from XX_ES.XX_ESExporter import ESExporter
# from XX_ES.XX_ESImporter import ESImporter
from tqdm import tqdm


class DataProcesser():

    _show_progress = False

    def __init__(self, importer, exporter):
        self._importer = importer
        self._exporter = exporter

    def _transform(self, data):
        return data

    def process(self):
        total_count = self._exporter.get_total_count()
        if self._show_progress:
            iter_list = tqdm(self._exporter.fetch_data(), total=total_count)
        else:
            iter_list = self._exporter.fetch_data()
        for data in iter_list:
            for trans_data in self._transform(data):
                self._importer.insert_to_es(trans_data)
        self._importer.commit_to_es()

    def set_show_progress(self, flag):
        self._show_progress = flag
