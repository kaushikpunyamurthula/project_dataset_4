from urllib.parse import urljoin
from threading import Thread
from queue import Queue
import requests
import sys, os

class Worker(Thread):
    """
    Thread executing tasks from a given tasks queue
    """

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except:
                # An exception happened in this thread
                pass
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()


class ThreadPool:
    """
    Pool of threads consuming tasks from a queue
    """

    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """
        Add a task to the queue
        """

        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        """
        Add a list of tasks to the queue
        """

        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        """
        Wait for completion of all the tasks in the queue
        """

        self.tasks.join()


class ImgScrapy:
    """
    Image scraper class
    """

    def __init__(self, page_url, directory, injected, nfirst, nthreads, head, timeout):
        self.img_count = 0
        self.downloaded_links = []
        self.failed_links = []
        self.directory = directory
        self.download_directory = os.path.join(
            directory, page_url.split('/')[2])
        self.processed_count = 0
        self.max_threads = nthreads

    def download_img(self, image_link, file_location, pb):
        """
        Method to download an image
        """

        if '?' in file_location:
            file_location = file_location.split('?')[-2]
            
        try:
            image_request = requests.get(image_link, stream=True)
            if image_request.status_code == 200:
                with open(file_location, 'wb') as f:
                    f.write(image_request.content)
                self.downloaded_links.append(image_link)
                self.processed_count+=1
                pb.update(self.processed_count)
            else:
                self.failed_links.append(image_link)
                self.processed_count+=1
                pb.update(self.processed_count)
        except:
            self.failed_links.append(image_link)
            self.processed_count+=1
            pb.update(self.processed_count)

    def download_images(self, path, links):
        """
        Method to download images given a list of urls
        """

        if not os.path.exists(self.download_directory):
            try:
                os.makedirs(self.download_directory)
            except:
                print("Directory not found")


        self.img_links = links
        total_count = len(self.img_links)
        if self.download_first_n:
            self.img_links = self.img_links[:self.download_first_n]

        self.img_count = len(self.img_links)

        pool_size = max(self.img_count, self.max_threads)
        pool = ThreadPool(pool_size)

        for link in self.img_links:
            file_location = self.download_directory+"/" + \
                link.split('/')[len(link.split('/'))-1]
            pool.add_task(self.download_img, link, file_location)

        pool.wait_completion()
