import warc
from utils import Utils
from constants import warc_path_file,segments,cc_base_url
import os

img_data = []
utils = Utils()
warc_file_paths = utils.get_warc_file_paths(segments, warc_path_file)
warc_count=0

WARC_LIMIT = 2

for segment in segments:
    print("\nProcessing segment %s\n" % segment)
    for warc_ in warc_file_paths[segment]:
        path = warc_.split('/')
        warc_file = path[-1]
        path = '/'.join(path[:len(path)-1])
        # warc_file = './warc_files/CC-MAIN-20210723210216-20210724000216-00000.warc.gz'
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                print("Directory not found")
        if not os.path.exists(warc_):
            utils.download_warc(cc_base_url, warc_)
        img_data = utils.process_warc('./' + warc_, segment)
        data_len = len(img_data)
        print(data_len)
        os.remove(warc_)

        warc_count+=1
        if warc_count>=WARC_LIMIT:
            break

utils.write_to_csv(img_data)