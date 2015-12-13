import time
# import datetime
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import logging.handlers
import os
# import platform
# import subprocess
# import random

LOGGER_FORMAT_START = '%(asctime)-15s\t%(levelno)d\t%(levelname)s\t'


class Twitter_scrapper():
    tweets_number=0
    """
    Tweeter scraper
    """
    def __init__(self, webdriver, log_name=''):
        if log_name == '':
            log_name = r'D:\TwitterDB\twitter_log.tsv'

        self.driver = webdriver
        self.driver.implicitly_wait(7) # seconds
        self.log = logging.getLogger('twitter')
        hndl1 = logging.StreamHandler()
        formatter = logging.Formatter(LOGGER_FORMAT_START + '%(username)-15s\t%(message)s')
        hndl1.setFormatter(formatter)
        if log_name:
            hndl2 = logging.FileHandler(log_name)
            hndl2.setFormatter(formatter)
            self.log.addHandler(hndl2)

        self.log.addHandler(hndl1)
        self.log.setLevel(logging.INFO)
        self.log_extra = {'username' : 'Not Set'}
        self.tweets = []

    """
    Login into tweeter account
    """
    def login(self, username, passwd):
       
        self.log_extra['username'] = username
        self.log.info('Trying to log in as  {%s}:{%s}'%(username,passwd), extra=self.log_extra)
        self.driver.get("http://twitter.com/login")
        try:
            username_element = self.driver.find_elements(By.XPATH, "//input[contains(@name,'session[username_or_email]')]")[1]
            username_element.send_keys(username)
            time.sleep(0.7)
            password_element = self.driver.find_elements(By.XPATH, "//input[contains(@name,'session[password]')]")[1]
            password_element.send_keys(passwd)
            time.sleep(0.3)
            btn = self.driver.find_elements(By.XPATH, "//button[contains(@class,'submit btn primary-btn')]")[0]
            btn.click()
            time.sleep(5)
            if 'login/error?' in self.driver.current_url:
                self.log.warn('Login failed', extra=self.log_extra)
                return False
        except TimeoutException:
            self.log.warn('Page load timeout reached', extra=self.log_extra)
            return False
        except IndexError:
            self.log.warn('Expected web page element not found', extra=self.log_extra)
            return False
        self.log.info('Login done', extra=self.log_extra)
        return True

    """
    Waits for update bar until timeout (in seconds)
    """
    def wait4update(self, timeout=60):
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            clickNewTweets = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'new-tweets-bar js-new-tweets-bar')]")))
            self.log.info('Update bar detected => ' + clickNewTweets.text, extra=self.log_extra)
            clickNewTweets.click()
            return True
        except (TimeoutException, NoSuchElementException):
            #self.log.info('Page load timeout reached', extra=self.log_extra)
            # self.log.info('Waiting 30 seconds to retry', extra=self.log_extra)
            return False

    """
    Process Tweeter main page, log previously unseen tweets
    """
    def process_page(self, empty_run=False):

        msg_lst = self.driver.find_elements(By.XPATH, "//div[contains(@class,'tweet original-tweet js-original-tweet js-stream-tweet')]")
        if msg_lst:
            self.log.info('Processing %d tweets'%len(msg_lst), extra=self.log_extra)
        count = 0
        for msg in msg_lst:
            tweet_id = msg.get_attribute('data-tweet-id')
            poster_name = msg.get_attribute('data-screen-name')
            tweet_text = msg.find_element(By.XPATH, './/p').text
            if tweet_id not in self.tweets:
                self.tweets.append(tweet_id)
                if not empty_run:
                    self.log.info('!!\t' + tweet_id + '\t' + poster_name + '\t' + tweet_text, extra=self.log_extra)
                    count += 1
            else:
                break
        if count:
            self.log.info('Only %d out of %d are new tweets'%(count, len(msg_lst)), extra=self.log_extra)
            self.tweets_counter(count)

    """
    Consumes data from twitter page until timeout (in minutes).
    Returns False on error.
    """
    def consume(self, timeout=60):
        
        if timeout<60:
            self.log.info('Consuming for %d minutes'%timeout, extra=self.log_extra)
        else:
            self.log.info('Consuming for %d:%d '%(timeout/60, timeout%60), extra=self.log_extra)


        expected_URL = 'https://twitter.com/'
        if self.driver.current_url != expected_URL:
            self.log.warn('Unexpected URL ("%s")'%self.driver.current_url, extra=self.log_extra)
            return False
        self.process_page(empty_run=True)
        t = time.time()

        while (time.time()-t)/60 < timeout:
            while not self.wait4update():
                if (time.time()-t)/60 > timeout:
                    break
            self.process_page()
            if Twitter_scrapper.tweets_number >= 300:
                Twitter_scrapper.tweets_number = 0
                break

        self.log.info('Consuming finished', extra=self.log_extra)
        return True

    """
    """

    def consume_by_time(self,timeout=60,refresh=3):
        if timeout<60:
            self.log.info('Consuming for %d minutes'%timeout, extra=self.log_extra)
        else:
            self.log.info('Consuming for %d:%d '%(timeout/60, timeout%60), extra=self.log_extra)


        expected_URL = 'https://twitter.com/'
        if self.driver.current_url != expected_URL:
            self.log.warn('Unexpected URL ("%s")'%self.driver.current_url, extra=self.log_extra)
            return False
        self.process_page(empty_run=True)
        t = time.time()

        while (time.time()-t)/60 < timeout:
            
            if self.wait4update():
                self.process_page()
            time.sleep(60*refresh)

        self.log.info('Consuming finished', extra=self.log_extra)
        return True

    """
    The function adds photos(s) to tweet.
    """
    def _add_photo(self, pic_path):
        
        if pic_path:
            if os.path.exists(pic_path):
                self.log.info('Adding photo:\t'+pic_path, extra=self.log_extra)
                tweetPic = self.driver.find_elements(By.XPATH, "//*[contains(@class,'file-input')]")[1]
                #tweetPic.click() # clicking invokes file selection dialog window
                tweetPic.send_keys(pic_path)
            else:
                self.log.warn('Photo file does not exist : %s'%pic_path, extra=self.log_extra)

    """
    This function will count the number off tweets and print the total number into the log file
    """
    def tweets_counter(self,count):
        Twitter_scrapper.tweets_number = Twitter_scrapper.tweets_number + count
        self.log.info('tweet number: %d\t'%Twitter_scrapper.tweets_number, extra=self.log_extra)

    
    """
    The function posts a tweet.
    """
    def make_tweet(self, tw_text, pic_path=''):
        
        try:
            wait = WebDriverWait(self.driver, 2)
            tweetTextBox = wait.until(EC.element_to_be_clickable((By.ID, "tweet-box-home-timeline")))
            tweetTextBox.click()

            tw_text = tw_text[:116]  # cut off tweet text
            if tw_text:
                self.log.info('Adding text:\t'+tw_text, extra=self.log_extra)
                #tweetTextBox.clear()
                tweetTextBox.send_keys(tw_text)

            if type(pic_path) is tuple or type(pic_path) is list:
                for pic in pic_path:
                    self._add_photo(pic)
            elif type(pic_path) is str:
                    self._add_photo(pic_path)

            self.log.info('Locating "Tweet" button', extra=self.log_extra)
            wait = WebDriverWait(self.driver, 10)
            sendTweet =  wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'primary-btn tweet-action tweet-btn')]")))
            sendTweet.click()

            self.log.info('Clicked! Confirming post', extra=self.log_extra)
            wait_timeout = 90  # sec
            cnt = wait_timeout*10
            while cnt>0:
                if not sendTweet.is_displayed():
                    self.log.info('$$ Posted! (after %.1f sec)'%(wait_timeout-cnt/10.0), extra=self.log_extra)
                    self.tweets_counter()
                    break
                cnt -= 1
                time.sleep(0.1)
            else:
                self.log.warn('Timeout reached (Browser is stalled ?)', extra=self.log_extra)
                # search for alert window
                error_msg = self.driver.find_element(By.CLASS_NAME, "message-text")
                if error_msg.is_displayed():
                    self.log.warn('$$ Error: '+error_msg.text, extra=self.log_extra)
                else:
                    # check if ready for next tweet.
                    twt_box = tweetTextBox.find_element(By.XPATH, "parent::*/parent::*")
                    if 'condensed' in twt_box.get_attribute('class'):
                        return True
                    self.log.warn('$$ Unknown error', extra=self.log_extra)
                #tweetTextBox.clear()
                return False

        except (TimeoutException, NoSuchElementException):
            self.log.warn('$$ Posting new tweet failed', extra=self.log_extra)
            return False

        return True
