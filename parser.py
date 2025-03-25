import re
import os
import pickle
import json
import time
from multiprocessing import Pool

from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import WebDriverException
from fake_useragent import UserAgent
from index import download_video

# Constants
GECKO_DRIVER_PATH = os.path.join(os.getcwd(), "geckodriver.exe")
COOKIES_FILE = "cookies"
NAME_AND_URL_JSON = "name_and_url"
VIDEO_WITH_ID_JSON = "filename_video_with_id"
PROGRAM_URL = "https://netology.ru/profile/program/ajs-46/schedule"
AUTHENTICATION_URL = "https://netology.ru/?modal=sign_in"
NUM_PROCESSES = 10

# User agent setup
ua = UserAgent()
user_agent = ua.random
headers = {"accept": "*/*", "user-agent": user_agent}


class WebDriver:
    def __init__(self):
        self.driver = None

    def initialize(self):
        service = Service(executable_path=GECKO_DRIVER_PATH)
        options = webdriver.FirefoxOptions()
        options.set_preference("general.useragent.override", user_agent)
        options.add_argument("--headless=old")
        self.driver = webdriver.Firefox(options=options, service=service)

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver.quit()


def get_cookies():
    """Get cookies."""
    try:
        driver = WebDriver()
        driver.initialize()
        driver = driver.driver
        driver.get(url=AUTHENTICATION_URL)
        time.sleep(5)
        email_input = driver.find_element(By.NAME, "email")
        email_input.clear()
        email_input.send_keys("daniil_vasilenko757@mail.ru")
        time.sleep(5)
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("Wither757!")
        password_input.send_keys(Keys.ENTER)
        time.sleep(20)
        pickle.dump(driver.get_cookies(), open(COOKIES_FILE, "wb"))
        print("Cookies saved to file:", COOKIES_FILE)
    except Exception as ex:
        print("Error while getting cookies:", ex)


def authorized_session(driver, url):
    """Create an authorized session."""
    try:
        driver.get(url=url)
        for cookie in pickle.load(open(COOKIES_FILE, "rb")):
            driver.add_cookie(cookie)
        driver.refresh()
    except Exception as ex:
        print("Error in authorized session:", ex)


def get_links(driver, url, name_class_block):
    """Get links to webinars or recorded videos on the website."""
    try:
        xpath_block = f'//div[@class="{name_class_block}"]'
        data = []
        driver.initialize()
        authorized_session(driver.driver, url)
        driver.driver.implicitly_wait(60)
        list_elements = driver.driver.find_elements(By.XPATH, xpath_block)
        for element in tqdm(list_elements, desc="Clicking blocks...", unit="process"):
            element.click()
        elements_video = driver.driver.find_elements(By.XPATH, '//div[@class="src-components-lms-shared-LessonItemIcon--root--ARxp7"]//ancestor::a')
        elements_webinar = driver.driver.find_elements(By.XPATH, '//div[@class="src-components-lms-shared-LessonItemIcon--root--ARxp7 src-components-lms-shared-LessonItemIcon--webinar--xpsv0"]//ancestor::a')
        elements = elements_video + elements_webinar
        for element in elements:
            name = element.find_element(By.XPATH, './/div[@class="src-features-lms-lessons-components-Lessons-components-Lesson-components-LessonItems--itemTitle--qBEs_"]').text
            url = element.get_attribute("href")
            data.append({"name": replace_path(name), "url": url})
        return data
    except Exception as ex:
        print("Error in get_links:", ex)
    finally:
        driver.close()


def write_to_json(data, name):
    """Write data to JSON file."""
    with open(f"{name}.json", "w") as file:
        json.dump(data, file, indent=4)


def read_from_json(name):
    """Read data from JSON file."""
    with open(f"{name}.json", "r") as file:
        return json.load(file)


def replace_path(name):
    """Replace invalid characters in the name."""
    pattern = r"[^\w\d]+"
    replacement = "_"
    return re.sub(pattern, replacement, name)


def get_video_id(args):
    """Get video ID."""
    driver, url, name = args
    xpath_video = 'iframe[src]'
    try:
        driver.initialize()
        authorized_session(driver.driver, url)
        driver.driver.implicitly_wait(60)
        video_url = driver.driver.find_element(By.CSS_SELECTOR, xpath_video).get_attribute('src')
        video_id = video_url.split('?', 1)[0].split('/')[-1]
        return {'url': video_id, 'name': name}
    except WebDriverException as ex:
        print("Error in get_video_id:", ex)
        print("URL:", url)
    finally:
        driver.close()


def extract_and_save_links(url):
    """Extract and save links."""
    driver = WebDriver()
    links_to_webinar = get_links(driver, url, "src-features-lms-lessons-components-Lessons-components-Lesson--root--_9T5o")
    write_to_json(links_to_webinar, NAME_AND_URL_JSON)


def process_links_from_file():
    """Process links from file."""
    list_url_video = read_from_json(NAME_AND_URL_JSON)
    driver = WebDriver()
    with Pool(NUM_PROCESSES) as p:
        video_ids = list(tqdm(p.imap(get_video_id, [(driver, item['url'], item['name']) for item in list_url_video]), desc="Parsing video IDs", total=len(list_url_video), unit="process"))
    write_to_json(video_ids, VIDEO_WITH_ID_JSON)


def main():
    # get_cookies()
    # extract_and_save_links(PROGRAM_URL)
    # process_links_from_file()
    # for item in read_from_json(VIDEO_WITH_ID_JSON):
    #     download_video(item['url'], replace_path(item['name']))
    import os
    import requests
    import subprocess
    from xml.etree import ElementTree

    def download_kinescope(mpd_url, output_file):
        response = requests.get(mpd_url)
        if response.status_code != 200:
            print("Ошибка загрузки MPD-файла")
            return

        tree = ElementTree.fromstring(response.content)
        namespace = {'mpd': 'urn:mpeg:dash:schema:mpd:2011'}

        base_url = os.path.dirname(mpd_url) + '/'
        video_segments = []
        audio_segments = []

        # Находим видеосегменты (лучшее качество)
        adaptation_sets = tree.findall(".//mpd:AdaptationSet", namespace)
        for adaptation in adaptation_sets:
            mime_type = adaptation.get("mimeType", "")
            representations = adaptation.findall("mpd:Representation", namespace)
            best_representation = max(representations, key=lambda x: int(x.get("bandwidth", 0)))

            base_segment_url = best_representation.find("mpd:BaseURL", namespace).text
            segment_urls = [base_url + base_segment_url]

            if "video" in mime_type:
                video_segments.extend(segment_urls)
            elif "audio" in mime_type:
                audio_segments.extend(segment_urls)

        os.makedirs("segments", exist_ok=True)

        def download_segments(segments, folder, name):
            for i, url in enumerate(segments):
                file_path = os.path.join(folder, f"{name}_{i}.mp4")
                if not os.path.exists(file_path):
                    print(f"Скачивание {url}")
                    with open(file_path, "wb") as f:
                        f.write(requests.get(url).content)

        download_segments(video_segments, "segments", "video")
        download_segments(audio_segments, "segments", "audio")

        # Объединение в один файл
        video_files = "|".join([f"segments/video_{i}.mp4" for i in range(len(video_segments))])
        audio_files = "|".join([f"segments/audio_{i}.mp4" for i in range(len(audio_segments))])

        ffmpeg_cmd = f"ffmpeg -i 'concat:{video_files}' -i 'concat:{audio_files}' -c copy {output_file}"
        subprocess.run(ffmpeg_cmd, shell=True)

        print(f"Видео сохранено как {output_file}")

    # Пример использования
    download_kinescope("https://kinescope.io/9102e17e-a21c-49a3-9f07-5e0cfdbe8045/master.mpd", "output.mp4")


if __name__ == "__main__":
    main()
