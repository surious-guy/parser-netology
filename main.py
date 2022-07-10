from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from multiprocessing import Pool
from tqdm import tqdm
from selenium.common.exceptions import WebDriverException
import time
import pickle
import json
import os

ua = UserAgent()
user_agent = ua.random

headers = {
    "accept": "*/*",
    "user-agent": user_agent
}


def initialization_driver():
    """Инициализация сессии"""

    options = webdriver.FirefoxOptions()
    options.set_preference("general.useragent.override", user_agent)
    options.headless = False  # Включение фонового режима
    return webdriver.Firefox(
        executable_path=os.getcwd() + f"\\geckodriver.exe",
        options=options)


def get_cookies(driver, url):
    """Получение куки"""

    try:
        driver.get(url=url)
        time.sleep(5)
        email_input = driver.find_element_by_name("email")
        email_input.clear()
        email_input.send_keys("daniil_vasilenko757@mail.ru")
        time.sleep(5)
        password_input = driver.find_element_by_name("password")
        password_input.clear
        password_input.send_keys("Wither757!")
        password_input.send_keys(Keys.ENTER)
        time.sleep(20)
        pickle.dump(driver.get_cookies(), open("cookies", "wb"))
        print("Cookies записаны в файл cookies")
    except Exception as ex:
        print(ex)


def authorized_session(driver, url="https://netology.ru/profile/program/html-66/schedule"):
    """Получение авторизованной сессии"""

    try:
        driver.get(url=url)
        time.sleep(3)
        for cookie in pickle.load(open(os.getcwd() + "\\cookies", "rb")):
            driver.add_cookie(cookie)
        time.sleep(3)
        driver.refresh()
        time.sleep(3)
    except Exception as ex:
        print(ex)


def write_to_json(data, name):
    with open(f"{name}.json", "w", encoding="UTF-8") as file:
        json.dump(data, file, indent=4)


def create_dict_for_links(driver):
    xpath = '//div[@class="src-components-lms-LmsHeader--professionModuleName--jBZd4"]/span'
    name_dict = driver\
        .find_element(By.XPATH, xpath)\
        .text\
        .replace(":", "_")
    path = os.getcwd() + f"\\{name_dict}"
    try:
        os.mkdir(path)
        print("Успешно создана директория %s" % path)
    except OSError as ex:
        print(ex)
        print("Создать директорию %s не удалось" % path)
    finally:
        return name_dict


def get_links_to_webinars():
    """Получение ссылок на вебинары на сайте Нетологии"""
    try:
        data = []
        driver = initialization_driver()
        authorized_session(driver)
        name_dict = create_dict_for_links(driver)
        list_elements = driver.find_elements(By.XPATH,
                                             '//div[@class="src-features-lms-lessons-components-Lessons-components-Lesson--root--_9T5o"]')
        for element in tqdm(list_elements, desc="Parsing links...", unit="process"):
            element.click()
            for bottom_element in element\
                    .find_elements(By.XPATH, './/div[@class="src-features-lms-lessons-components-Lessons-components-Lesson-components-LessonItems--itemIcon--R9iLz"]//ancestor::a'):
                data.append(
                    {
                        "url": bottom_element.get_attribute("href")
                    }
                )
        write_to_json(data, "data_url_netology")
        return name_dict
    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()


def get_list_url(name):
    """Получение списка со ссылками на вебинары на сайте Нетологии"""
    with open(f"{name}.json", "r", encoding="UTF-8") as file:
        data = json.load(file)
    return [item["url"] for item in data if isinstance(item, dict)]


def get_list_name(name):
    """Получение списка со ссылками на вебинары на сайте Нетологии"""
    with open(f"{name}.json", "r", encoding="UTF-8") as file:
        data = json.load(file)
    return [item["name"] for item in data if isinstance(item, dict)]


def get_link_to_kinescope_webinar(url):
    """Получение вебинара на сайт kinescope с Нетологии"""
    exceptions = []
    try:
        driver = initialization_driver()
        authorized_session(driver, url)
        time.sleep(10)
        url_video = driver.find_element(By.XPATH,
                                        './/div[@class="src-components-common-KinescopePlayer2--iframeWrapper--GJ0Ou"]/iframe').get_attribute("src")
        name = driver.find_element(By.XPATH,
                                   './/div[@class="src-components-lms-shared-LessonItemHeading--title--LeDp6"]/div').text
        return {
            "name": name,
            "url": url_video
        }
    except Exception as ex:
        exceptions.append(f"{ex}\n\tURL-exception: {url}\n")
    finally:
        driver.close()
        driver.quit()
    for exception in exceptions:
        print(exception)


def write_name_video_to_txt(name_dict, list_name):
    """Запись в файл прямой ссылки на видео"""
    with open(f"{name_dict}\\name_video.txt", "w", encoding="UTF-8") as file:
        print(*list_name, file=file, sep="\n")


def write_url_video_to_txt(name_dict, list_url):
    """Запись в файл прямой ссылки на видео"""
    with open(f"{name_dict}\\url_video.txt", "w", encoding="UTF-8") as file:
        print(*list_url, file=file, sep="\n")


def write_url_audio_to_txt(name_dict, list_url):
    """Запись в файл прямой ссылки на аудио"""
    with open(f"{name_dict}\\url_audio.txt", "w") as file:
        print(*list_url, file=file, sep="\n")


def get_url_video(url):
    """Получение прямой ссылки на видео с вебинара"""
    pats = ("1080p.mp4", "720p.mp4", "480p.mp4", "360p.mp4")
    try:
        driver = initialization_driver()
        driver.get(url=url)
        time.sleep(3)
        driver.find_element(By.XPATH, "/html/body").click()
        driver.find_element(By.XPATH, "/html/body").send_keys("k")
        for pat in pats:
            try:
                url = driver.wait_for_request(pat).url
                return url
            except WebDriverException:
                continue
    except WebDriverException as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()


def get_url_audio(url):
    """Получение прямой ссылки на аудио с вебинара"""
    try:
        driver = initialization_driver()
        driver.get(url=url)
        time.sleep(3)
        driver.find_element(By.XPATH, "/html/body").click()
        driver.find_element(By.XPATH, "/html/body").send_keys("k")
        pat_audio = "audio_0.mp4"
        return driver.wait_for_request(pat_audio).url
    except WebDriverException:
        driver.quit()
        get_url_audio(url)
    finally:
        driver.close()
        driver.quit()


def main():
    name_dict = get_links_to_webinars()
    # print(name_dict)
    #
    # list_url = get_list_url("data_url_netology")
    #
    # with Pool(5) as p:
    #     data = list(tqdm(p.imap(get_link_to_kinescope_webinar, list_url),
    #                      desc="Парсинг ссылок на kinescope",
    #                      total=len(list_url),
    #                      unit="process"))
    # write_to_json(data, "name_and_url")
    #
    # list_name = get_list_name("name_and_url")
    # write_name_video_to_txt(name_dict, list_name)
    #
    list_url = get_list_url("name_and_url")
    #
    # with Pool(5) as p:
    #     data = list(tqdm(p.imap(get_url_video, list_url),
    #                      desc="Парсинг ссылок на видео",
    #                      total=len(list_url),
    #                      unit="process"))
    # write_url_video_to_txt(name_dict, data)

    with Pool(5) as p:
        data = list(tqdm(p.imap(get_url_audio, list_url),
                         desc="Парсинг ссылок на аудио",
                         total=len(list_url),
                         unit="process"))
    write_url_audio_to_txt(name_dict, data)


if __name__ == "__main__":
    main()
