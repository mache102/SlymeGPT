from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions as selexcept

import configparser
import functools
import os
import sys
import time
import undetected_chromedriver as uc

from slyme_utils import *

UNTITLED_PLACEHOLDER = '[recently generated chat]'

def driver_refresh(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        self.driver.implicitly_wait(self.wait_sec)
        time.sleep(1)
        try:
            return func(self, *args, **kwargs)
        except selexcept.WebDriverException as e:
            if str(e).strip() == 'Message: disconnected: not connected to DevTools':
                self.logger.warning('WebDriver timed out. Refreshing page')
                self.driver.refresh()
                self.driver.implicitly_wait(self.wait_sec)
                if self.selected_chat != None:
                    if self.selected_chat == UNTITLED_PLACEHOLDER:
                        self.select_latest_chat()
                    else:
                        self.select_chat(self.selected_chat)
                return func(self, *args, **kwargs)  
            else:
                raise e  
    return wrapper

class ChatMain:
    @driver_refresh
    def completion(self, prompt, interval=0.1, recheck_delay=5):
        self.enter_field(type=By.CLASS_NAME, 
                         name=self.config.get('class', 'prompt_field'), 
                         input=prompt)
        
        repeat_success(self.await_element)
        self.logger.debug('Response element detected')
        repeat_success(self.await_response)
        self.logger.debug('Response text located')

        elements = self.driver.find_elements(By.CLASS_NAME, self.config.get('class', 'GPT_response_history'))
        status = 1

        while status:
            status = self.check_generator(elements)

            if status == False:
                self.logger.debug(f'Single occurrence of "::after" pseudo-element not found.')
                for i in range(10):
                    time.sleep(0.1)
                    self.driver.implicitly_wait(recheck_delay)
                    elements = self.driver.find_elements(By.CLASS_NAME, self.config.get('class', 'GPT_response_history'))
                    status = self.check_generator(elements)

                    if status == True: 
                        self.logger.debug(f'Pseudo-element found after element update. Continuing checks as normal.')
                        break
                    else:
                        self.logger.debug(f'Pseudo-element not found after element update ({i+1}). The response may or may not have finished generating; please check its completeness in case of an abnormality.')

            time.sleep(interval)

        response = elements[-1].text
        char_limited_response = char_limiter(response)

        self.selected_chat = UNTITLED_PLACEHOLDER
        self.logger.info(f'Response successfully generated: "{char_limited_response}"')

        return response

    def await_element(self):
        """
        Wait for element to appear
        """
        elements = self.driver.find_elements(By.CLASS_NAME, self.config.get('class', 'GPT_response_history'))
        self.last_response = elements[-1]
        

    def await_response(self):
        """
        Wait for response to appear
        """
        self.last_response.text

    def property_script(self, property):
        return f"""
                const element = arguments[0];
                const property = window.getComputedStyle(element, "{property}").getPropertyValue("content");
                return property !== "" && property !== "none";
        """
    
    def check_generator(self, elements):
        sub_elements = elements[-1].find_elements(By.CSS_SELECTOR, "*")
        is_generating = False 
        
        # Check from the last element, where the generator is more likely to be present
        for sub_element in sub_elements[::-1]:
            try:
                has_before = self.driver.execute_script(self.property_script('::before'), sub_element)
                has_after = self.driver.execute_script(self.property_script('::after'), sub_element)
            except Exception as e:
                #selexcept.StaleElementReferenceException or selexcept.WebDriverException:
                self.logger.warning(f'Encountered an {type(e).__name__}. This might occur if an element is checked during an update. Continuing checks as normal.')
                is_generating = True 
                break 

            if has_after and not(has_before):
                is_generating = True 
                break 

        return is_generating
    
    @driver_refresh
    def find_entry(self, type, index):
        if self.selected_chat == None:
            self.logger.error('No chat selected. Please select a chat first.')
            return
        
        if type == 'prompt':
            class_name = self.config.get('class', 'USR_prompt_history')
            slicer = slice(None, None, 2)
        elif type == 'response':
            class_name = self.config.get('class', 'GPT_response_history')
            # slicer = slice(1, None, 2)
        else:
            self.logger.error(f'Invalid type {type}.')
            return

        result_elements = self.driver.find_elements(By.CLASS_NAME, class_name)

        if type == 'prompt':
            result_elements = result_elements[slicer]

        try:
            result = result_elements[index].text
            self.logger.debug(f'{type.capitalize()} found for index {index} in chat "{self.selected_chat}"')
            return result
        except Exception:
            self.logger.error(f'Index overflow or text not found in element')

class ChatSidebar:
    def get_proj(self, element):
        return element.get_attribute(self.config.get('attr', 'data_proj_id'))
    
    @driver_refresh
    def new_chat(self):
        chat_element = self.driver.find_element(By.XPATH, "//a[contains(text(), 'New chat')]")
        chat_element.click()
        self.logger.debug('Successfully created new chat')

        self.selected_chat = None
    
    @driver_refresh
    def select_chat(self, chat_name):
        chat_elements = self.driver.find_elements(By.CSS_SELECTOR, self.config.get('css', 'chat_elements'))
        for chat_element in chat_elements:
            if chat_element.text == chat_name:
                chat_element.click()

                data_proj_id = self.get_proj(chat_element)
                self.selected_chat = chat_name
                self.logger.debug(f'Selected found chat. Name: "{chat_name}", Data Proj ID: "{data_proj_id}"')
                return data_proj_id
            
        self.logger.error(f'No chat found: "{chat_name}"')
        return False
        
    @driver_refresh
    def select_latest_chat(self):
        chat_element = self.driver.find_element(By.CSS_SELECTOR, self.config.get('css', 'chat_elements'))
        chat_element.click()

        self.selected_chat = chat_element.text
        self.logger.debug(f'Selected latest chat. Name: "{chat_element.text}", Data Proj ID: "{self.get_proj(chat_element)}"')

    @driver_refresh
    def rename_chat(self, chat_name, new_name):
        chat_status = self.select_chat(chat_name) 
        if chat_status == False:
            return

        chat_edit_tools = self.driver.find_element(By.CLASS_NAME, 'absolute.flex')
        rename_chat = chat_edit_tools.find_elements(By.CSS_SELECTOR, "*")
        rename_chat[0].click()

        rename_element = self.driver.switch_to.active_element
        rename_element.send_keys(Keys.BACKSPACE * len(chat_name))
        rename_element.send_keys(new_name)
        rename_element.send_keys(Keys.ENTER)
        
        self.selected_chat = new_name
        self.logger.debug(f'Successfully renamed chat: "{chat_name}" to "{new_name}"')

    """
    The deletion confirmation click doesn't work for some reason
    def delete_chat(self, chat_name):
        chat_status = self.select_chat(chat_name) 
        if chat_status == False:
            return

        chat_edit_tools = self.driver.find_element(By.CLASS_NAME, 'absolute.flex')
        delete_chat = chat_edit_tools.find_elements(By.CSS_SELECTOR, "*")
        delete_chat[1].click()

        chat_edit_tools = self.driver.find_element(By.CLASS_NAME, 'absolute.flex')
        confirm_delete = chat_edit_tools.find_elements(By.CSS_SELECTOR, "*")

        confirm_delete[0].click()
        self.logger.debug(f'Successfully deleted chat: "{chat_name}"')
        
    """

    @driver_refresh
    def get_chat_names(self):
        chat_elements = self.driver.find_elements(By.CSS_SELECTOR, self.config.get('css', 'chat_elements'))
        self.logger.debug(f'Found {len(chat_elements)} chats.')

        for idx, chat_element in enumerate(chat_elements):
            self.logger.debug(f'Chat {idx + 1}, Name: "{chat_element.text}", Data Proj ID: "{self.get_proj(chat_element)}"')


class SlymeDriver(ChatMain, ChatSidebar):
    def __init__(self, pfname='Default', debug=False, wait_sec=60):
        self.wait_sec = wait_sec        
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.logger = log_setup(self.config.get('dir', 'log_file'),
                                console_level=None)
        self.selected_chat = None
        
        self.get_driver(pfname)
        self.driver.get("https://chat.openai.com")
        self.driver.implicitly_wait(self.wait_sec)
        if debug == False:
            self.driver.minimize_window()
        self.logger.info('Ready')
    
    def get_driver(self, pfname):
        options = webdriver.ChromeOptions()

        if sys.platform == "win32":
            # Windows
            options.add_argument(f"--user-data-dir=C:/Users/{os.getlogin()}/AppData/Local/Google/Chrome/User Data/{pfname}")
        elif sys.platform == "darwin":
            # macOS
            options.add_argument(f"--user-data-dir=~/Library/Application Support/Google/Chrome/{pfname}")
        elif sys.platform.startswith("linux"):
            # Linux
            options.add_argument(f"--user-data-dir=~/.config/google-chrome/{pfname}")
        else:
            # Unsupported platform
            raise Exception("Unsupported platform")
    
        self.driver = uc.Chrome(options=options, use_subprocess=True)
        #self.driver.minimize_window()
        self.logger.info(f'Initialized Undetected Chromedriver')

    """
    def login(self):
        try:
            login_button = self.driver.find_element(By.CLASS_NAME, self.config.get('class', 'login'))
            login_button.click()
            msedge_button = self.driver.find_element(By.CLASS_NAME, self.config.get('class', 'login'))
            msedge_button.click()
            self.click_btn(type=By.CLASS_NAME, name=self.config.get('class', 'login'))
            self.click_btn(type=By.CLASS_NAME, name=self.config.get('class', 'msedge_btn'))

            self.enter_field(type=By.NAME, name=self.config.get('id', 'email'), 
                       input=self.config.get('secrets', 'email'))
            
            self.enter_field(type=By.NAME, name=self.config.get('id', 'password'), 
                       input=decode_base64(self.config.get('secrets', 'password')))
            
            self.logger.info('Successfully logged in!')
 
        except Exception:
            self.logger.info('Already logged in!')
            pass
    """

    def enter_field(self, type, name, input, 
                    sec=1, split_len=128):

        field = self.driver.find_element(type, name)

        # if len(input) > split_len:
        #     substr_list = []
        #     while len(input) > split_len:
        #         substr = input[:split_len]
        #         substr_list.append(substr)
        #         input = input[split_len:]
            
        #     substr_list.append(input)
        #     for substr in substr_list:
        #         field.send_keys(substr)
        # else:
        #     field.send_keys(input) 

        self.driver.execute_script("arguments[0].value = arguments[1]", field, input)
        field.send_keys(Keys.ENTER)

        char_limited_input = char_limiter(input)

        self.logger.debug(f'Entered input "{char_limited_input}". Element: "{type}", Name: "{name}"')

        time.sleep(sec)
    
    def screenshot(self, save_name):
        self.driver.save_screenshot(save_name)
        self.logger.info(f'Saved screenshot to {save_name}')

    def end_session(self):
        self.driver.quit()
        self.logger.info('Closed driver session')


