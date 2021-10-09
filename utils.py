from re import split
from lxml import html
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin
import wget
import warc
import uuid
from bs4 import BeautifulSoup
import os
import csv
from langdetect import detect, DetectorFactory
from constants import warc_path_file,segments,cc_base_url

class Utils:
    def __init__(self):
        pass
    
    def get_warc_file_paths(self,segments,paths_file):
        warc_file_paths = {}
        with open(paths_file) as f:
            for line in f:
                for segment in segments:
                    if segment in line:
                        if segment not in warc_file_paths:
                            warc_file_paths[segment]=[line.replace('\n','')]
                        else:
                            warc_file_paths[segment].append(line.replace('\n',''))
        return warc_file_paths

    def read_doc(self,record):
        url = record.url
        html_string = ''

        if url:
            payload = str(record.payload.read())
            header, html_string = payload.split('\r\n\r\n', 1)
        return url, html_string

    def acquire_links(self, html_doc, page_url, file_name, segment):
        """
        Method to get images' download links
        """
        DetectorFactory.seed = 0
        images = []
        soup = BeautifulSoup(html_doc, 'html.parser')
        img_tags = soup.find_all('img', alt = True, src = True)
        for img in img_tags:
            prev_ele = img.find_previous('p')
            next_ele = img.find_next('p')
            context_text = ''
            if prev_ele != None:
                context_text += prev_ele.getText()
            if next_ele != None:
                context_text += next_ele.getText()
            context_text.strip('\r').strip('\n').strip('\t')
            try:
                lang = detect(context_text)
            except:
                continue
            if context_text != '' and lang == 'en' and len(context_text) > 10:
                images.append({
                    "uuid": str(uuid.uuid4()),
                    "page_url": page_url,
                    "link": ("" + urljoin(page_url, img['src'])).encode("utf-8"),
                    "alt": img['alt'].encode("utf-8"),
                    "context": context_text.encode("utf-8"),
                    "warc file": file_name.split("/", -1)[2],
                    "segment": segment
                })
        return images

    def process_warc(self, file_name, segment):
        print("\n\nProcessing %s" % file_name)
        img_data = []
        warc_file = warc.open(file_name, 'rb')
        for i, record in enumerate(warc_file):
            url, html = self.read_doc(record)
            if html is '' or url is None:
                continue
            img_data+=self.acquire_links(html, url, file_name, segment)
        warc_file.close()
        return img_data

    def download_warc(self,base_url, path):
        wget.download(urljoin(base_url, path), path)

    def write_to_csv(img_data):
        csv_filename = "./images_data.csv"
        with open(csv_filename, 'wb') as csv_file:  
            writer = csv.writer(csv_file)
            writer.writerow(img_data[0].keys())
            for img_ele in img_data:
                writer.writerow(img_ele.values())