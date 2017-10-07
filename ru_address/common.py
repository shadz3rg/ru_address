import os
import re
import datetime

import math
import psutil


class Common:
    @staticmethod
    def build_ngrams(keyword, n=3, filler="__"):
        keyword_w_filler = filler + keyword + filler
        left_length = len(keyword_w_filler) - len(filler)

        trigrams = []
        for i in range(0, left_length):
            trigrams.append(keyword_w_filler[i:i + n])

        return " ".join(trigrams)

    @staticmethod
    def clear_keyword(keyword, regex=re.compile("[\s\"'\.,()\-_\\\/]")):
        keyword = regex.sub("_", keyword)
        return keyword.lower()

    @staticmethod
    def update_progress(workdone):
        # Отображает отформатированный прогресс-бар
        print("\r[{0:50s}] {1:.1f}% ".format('#' * int(workdone * 50), workdone * 100), end="", flush=True)

    @staticmethod
    def cli_output(message):
        print('[{}] {}'.format(datetime.datetime.now().time().isoformat(timespec='seconds'), message))

    @staticmethod
    def show_memory_usage():
        process = psutil.Process(os.getpid())
        print('Memory usage: {} mb'.format(round(process.memory_info().rss / 1024 / 1024, 2)))


class DataSource(object):
    def __init__(self, filename):
        self.size = os.path.getsize(filename)
        self.delivered = 0
        self.f = open(filename, 'r', encoding='utf-8')

    def read(self, size=None):
        if size is None:
            self.delivered = self.size
            return self.f.read()

        data = self.f.read(size)
        self.delivered += len(data)
        return data

    def close(self):
        self.f.close()

    @property
    def percentage(self):
        return float(self.delivered) / self.size * 100.0
