"""
multipart/form-data streaming example
"""
import requests
from clint.textui.progress import Bar as ProgressBar
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


class file_iterator(object):
    def __init__(self, url):
        self.req = requests.get(url, stream=True, timeout=512)
        self.req_gen = self.req.iter_content(8192)
        self._len = int(self.req.headers['Content-Length'])
        self._sent = 0

    def __len__(self):
        return self._len - self._sent

    def read(self, n):
        try:
            chunk = next(self.req_gen)
            self._sent += len(chunk)
            return chunk
        except StopIteration:
            self.req.close()
            return ''.encode()


def create_callback(encoder, total_size):
    bar = ProgressBar(expected_size=total_size, filled_char='=')

    def callback(monitor):
        bar.show(monitor.bytes_read)

    return callback


def create_upload(urls):
    total_size = []

    def form(total_size, url):
        r = requests.head(url, allow_redirects=True)
        total_size.append(int(r.headers.get('content-length')))
        return ('filename', file_iterator(url), r.headers.get('content-type'))

    return MultipartEncoder({
        f'file_{i}': form(total_size, url) for i, url in enumerate(urls)
    }), sum(total_size)


if __name__ == '__main__':
    encoder, total_size = create_upload(['https://file-examples.com/wp-content/uploads/2017/04/file_example_MP4_1920_18MG.mp4',
                                         'https://file-examples.com/wp-content/uploads/2017/11/file_example_MP3_2MG.mp3'])
    callback = create_callback(encoder, total_size)
    monitor = MultipartEncoderMonitor(encoder, callback)
    r = requests.post('https://dtf.ru/andropov/upload', data=monitor, headers={'Content-Type': monitor.content_type, "x-this-is-csrf": "THIS IS SPARTA!"})
    print(f'\nUpload finished! (Returned status {r.status_code} {r.reason})')
    print(r.json())
