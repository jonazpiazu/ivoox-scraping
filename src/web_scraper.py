import os

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.config import Config

from pyvirtualdisplay import Display


class WebScraper:

    def __init__(self, headless=True, muted=True):
        self.config = Config()
        self.headless = headless
        self.muted = muted

        # set xvfb display since there is no GUI in docker container.
        try:
            display = Display(visible=0, size=(800, 600))
            display.start()
        except Exception as e:
            print('Could not use xvfb display, will try to continue anyway. Error: {}'.format(e))

        self.options = self._set_webdriver_options
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=self.options)

    @property
    def _set_webdriver_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-extensions')
        if self.headless:
            options.add_argument("--headless")
        if self.muted:
            options.add_argument("--mute-audio")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return options

    def start_connection(self, url):
        self.driver.get(url)

        try:
            # Wait until the cookie banner button is clickable
            accept_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Agree') or contains(., 'Aceptar')]"))
            )
            accept_btn.click()
            print("Cookies accepted!")
        except Exception as e:
            print("No cookie banner found:", e)

    def click_element(self, element):
        try:
            self.driver.execute_script("arguments[0].click();", element)
        except WebDriverException:
            print('Element is not clickable')

    def find_element_by_partial_text(self, chapter_search_name):
        return self.driver.find_element(By.PARTIAL_LINK_TEXT, chapter_search_name)

    def find_element_by_xpath(self, xpath):
        return self.driver.find_element(By.XPATH, xpath)

    def find_elements_by_xpath(self, xpath):
        return self.driver.find_elements(By.XPATH, xpath)

    def find_element_by_id(self, html_id):
        return self.driver.find_element(By.ID, html_id)

    def close_connection(self):
        self.driver.quit()
