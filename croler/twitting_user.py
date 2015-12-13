import time
import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import os
import platform
import subprocess
from Twitter_scrapper_for_twitting import Twitter_scrapper

# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# import logging
# import random
# from selenium.webdriver.common.by import By


LOGGER_FORMAT_START = '%(asctime)-15s\t%(levelno)d\t%(levelname)s\t'

"""
Closes the browser, Tshark proc and log file
"""
def end_runing_func(tshark_proc,driver,tw):
    tshark_proc.kill()
    time.sleep(5)
    driver.quit()
    temp = list(tw.log.handlers)
    for i in temp:
        tw.log.removeHandler(i)
        i.flush()
        i.close()       

"""
Start and return Tshark process 
"""
def createPcap(filename):
    if platform.system() == 'Windows':
        tsharkCall = ["C:\\Program Files\\Wireshark\\tshark.exe","-F", "pcap", "-f", "tcp port 443", "-i", "1", "-w", filename]
    elif platform.system() == 'Linux':
        tsharkCall = ["/usr/bin/tshark","-F", "pcap", "-f", "tcp port 443", "-i", "2", "-w", filename]
    tsharkProc = subprocess.Popen(tsharkCall)
    return tsharkProc

"""
Initialize and return "driver" for the received "browser"
"""
def init_driver(browser):
    webdrv = {'ie':webdriver.Ie, 'chrome':webdriver.Chrome, 'ff':webdriver.Firefox, 'firefox':webdriver.Firefox}

    browser = str.lower(browser)
    if browser not in webdrv.keys():
        return None
    else:
        driver = webdrv[browser]()
        driver.wait = WebDriverWait(driver, 5)
    return driver

"""
create_log_name
"""
def create_log_name(browser_str, root_path):
    time_str = time.strftime("%m-%d__%H_%M_%S")

    if not os.path.exists(root_path):
        os.makedirs(root_path)

    os_name = platform.system()[0]
    host_name = platform.node()

    return root_path + os.sep + os_name + '_' + host_name + '_' + browser_str + "_" + time_str



"""
initialize and return log file, driver and tshark process 
"""
def start_driver_and_pcap():
    browser = 'chrome'
    db_path = r'd:\twitterdb'
    log_str = create_log_name(browser, db_path)

    # get Web Driver
    driver = init_driver(browser)

    # get TShark recording
    tshark_proc = createPcap(log_str + '.pcap')
    time.sleep(5)
    return log_str, driver, tshark_proc


"""**************************************************************************************************"""


"""
Tweets only text
This function tweets a time string every "num_of_tweet" seconds.
user_name = twitter user name
password= twitter password
num_of_tweet = total number of tweets
time_between_tweets = time between an individual Tweets (in seconds)
num_of_set = after this number of tweets will be a break of "break_time" seconds. 
break_time = time to wait between set of tweets. by default "break_time"=60
"""
def tweet_only_text(user_name, password, num_of_tweet, time_between_tweets, num_of_set, break_time = 60):
    log_str, driver, tshark_proc = start_driver_and_pcap()

    try:
                
        # login to Twitter
        tw = Twitter_scrapper(driver, log_str + '.tsv')
        if not tw.login(user_name, password):
            print 'Logging to Tweeter account failed'
            return
        dd = datetime.datetime.now()
        twttext = dd.strftime('Now is %Y-%m-%d %H:%M:%S +%f')
        if not tw.make_tweet(user_name+ twttext + '\n'):
                return
        time.sleep(time_between_tweets)
        for tweet_counter in range(num_of_tweet):
            # post tweets
            dd = datetime.datetime.now()
            twttext = dd.strftime('Now is %Y-%m-%d %H:%M:%S +%f')

            if not tw.make_tweet(twttext + '\n'):
                return
            
            time.sleep(time_between_tweets)
            if tweet_counter % num_of_set == 0:
                time.sleep(break_time - time_between_tweets)        

    finally:    # do cleaning anyway
        end_runing_func(tshark_proc,driver,tw)

"""
!!! this function unused for now
Get list of pictures folders paths and run "tweet_only_pic" for each path 
"""
def tweet_set_of_pic_by_path(username,password,path_arr, num_of_tweet, time_between_tweets, num_of_set, break_time):
    for op in path_arr:
        tweet_only_pic(username,password,num_of_tweet, time_between_tweets, num_of_set, break_time, op)

"""
Tweets only pictures
num_of_tweet = total number of tweets
time_between_tweets = time between an individual Tweets (in seconds)
num_of_set = after this number of tweets will be a break of "break_time" seconds. 
break_time = time to wait between set of tweets. by default "break_time"=60
pix_path = the path into the pictures folder. by default "pix_path"= r'D:\TwitterDB\diff_pic'
"""
def tweet_only_pic(user_name, password, num_of_tweet, time_between_tweets, num_of_set, break_time, pix_path):
    log_str, driver, tshark_proc = start_driver_and_pcap()


    try:
        # login to Twitter
        tw = Twitter_scrapper(driver, log_str + '.tsv')
        if not tw.login(user_name, password):
            print 'Logging to Tweeter account failed'
            return

        # get list of photos
        pix_names = []
        for filename in os.listdir(pix_path):
            if filename.lower().endswith('.jpg') or filename.lower().endswith('.png'):
                pix_names.append(pix_path + os.sep + filename)

        pic_cnt = 0
        for tweet_counter in range(0,num_of_tweet):
            pic = pix_names[pic_cnt]
            pic_cnt +=1
            if pic_cnt >= len(pix_names):
                pic_cnt = 0;
            
            if not tw.make_tweet('',pic):
                return
            print pic
            if Twitter_scrapper.tweets_number >= 700:
                break
            time.sleep(time_between_tweets)
            if tweet_counter % num_of_set == 0:
                time.sleep(break_time - time_between_tweets)   
            

    finally:    # do cleaning anyway
        end_runing_func(tshark_proc,driver,tw)

"""
Tweets pictures with text
user_name = twitter user name
password= twitter password
num_of_tweet = total number of tweets
time_between_tweets = time between an individual Tweets (in seconds)
num_of_set = after this number of tweets will be a break of "break_time" seconds. 
break_time = time to wait between set of tweets.
pix_path = the path into the pictures folder. by default "pix_path"= r'D:\TwitterDB\diff_pic'
"""    
def tweet_pic_with_text(user_name, password, num_of_tweet, time_between_tweets, num_of_set, break_time, pix_path):
    log_str, driver, tshark_proc = start_driver_and_pcap()
    
    
    try:
        # login to Twitter
        tw = Twitter_scrapper(driver, log_str + '.tsv')
        if not tw.login(user_name, password):
            print 'Logging to Tweeter account failed'
            return
        # get list of photos
        pix_names = []
        for filename in os.listdir(pix_path):
            if filename.lower().endswith('.jpg') or filename.lower().endswith('.png'):
                pix_names.append(pix_path + os.sep + filename)
                
        # first tweet with user name
        dd = datetime.datetime.now()
        twttext = dd.strftime('Now is %Y-%m-%d %H:%M:%S +%f')
        pic = pix_names[0]
        if not tw.make_tweet(user_name +' ' + twttext + '\n', pic):
                return
        time.sleep(time_between_tweets)        
        pic_cnt = 0
        for tweet_counter in range(0,num_of_tweet):
            #picture part
            pic = pix_names[pic_cnt]
            pic_cnt +=1
            if pic_cnt >= len(pix_names):
                pic_cnt = 0;
            # text part
            dd = datetime.datetime.now()
            twttext = dd.strftime('Now is %Y-%m-%d %H:%M:%S +%f')

            if not tw.make_tweet(twttext + '\n',pic):
                return
            print pic
            if Twitter_scrapper.tweets_number >= 700:
                break
            time.sleep(time_between_tweets)
            if tweet_counter % num_of_set == 0:
                time.sleep(break_time - time_between_tweets)
    
    
    finally:    # do cleaning anyway
        end_runing_func(tshark_proc,driver,tw)


    


if __name__ == "__main__":
    
    """ path list for pictures folders """
    path_list = [r'D:\TwitterDB\diff_pic\200 200', r'D:\TwitterDB\diff_pic\1000 1000', r'D:\TwitterDB\diff_pic\2000 2000']
    
    """ list of users for testing """
    #twitter_users = ['someonemeso','someonemeso']
    #twitter_passwords = ['q1w2e3r4','q1w2e3r4']
    
    """ list of useres for the crawler """
    twitter_users = ['mamecyber','mimacyber','moamacyber','tamacyberw','tamacyberg','timacyberg','timacyberw','tomacyberw','temacyberw','kemacyberw','kamacyberw','tweetComp@walla.co.il', 'mamegcyber', 'sib.kroll@gmail.com','momacyberg@walla.com','kimacyber@walla.com','komacyber@walla.co.il','ramacyber@walla.com','rimacyber@walla.com','rimacyberg@walla.com','remacyber@walla.com','romacyber@walla.com','samacyber@walla.com','simacyber@walla.com']
    twitter_passwords = ['ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','Info1Media', 'ASDFGH00', '1234qwer','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00','ASDFGH00']

    """ variable list """
    num_of_all_tweets = 300
    num_of_tweet = 300
    time_between_tweets = 180 #time in seconds between tweets
    num_of_set = 100
    break_time = 300

    
    """ run for tweet_only_text """
#   i= 0 
#   while i < (len(twitter_users)*4):
#       username = twitter_users[i % len(twitter_users)]
#       password = twitter_passwords[i % len(twitter_users)]
#       tweet_only_text(username,password,num_of_tweet,time_between_tweets,num_of_set,break_time)
#       i += 1 
#        if(Twitter_scrapper.tweets_number >= num_of_all_tweets):
#               Twitter_scrapper.tweets_number = 0
#               break  



    """ run for tweet_only_pic """

#     i= 0
#     for pix_path in path_list:        
#         while i < (len(twitter_users)*4):
#             username = twitter_users[i % len(twitter_users)]
#             password = twitter_passwords[i % len(twitter_users)]
#             tweet_only_pic(username, password, num_of_tweet, time_between_tweets, num_of_set, break_time,pix_path)
#             i += 1
#             if(Twitter_scrapper.tweets_number >= num_of_all_tweets):
#                 Twitter_scrapper.tweets_number = 0
#                 break
#         time.sleep(60)
    
    """ run for tweet_only_pic just on the specific images resolution"""

#     i= 0
#     pix_path = path_list[2]        
#     while i < (len(twitter_users)*4):
#         username = twitter_users[i % len(twitter_users)]
#         password = twitter_passwords[i % len(twitter_users)]
#         tweet_only_pic(username, password, num_of_tweet, time_between_tweets, num_of_set, break_time,pix_path)
#         i += 1
#         if(Twitter_scrapper.tweets_number >= num_of_all_tweets):
#             Twitter_scrapper.tweets_number = 0
#             break
#     time.sleep(60)


# 
    """ run for tweet_pic_with_text just on the 2000*2000 images"""
    pix_path_2000 = path_list[2]        
     
    i=5
    while i < (len(twitter_users)*4):
        username = twitter_users[i % len(twitter_users)]
        password = twitter_passwords[i % len(twitter_users)]
        tweet_pic_with_text(username, password, num_of_tweet, time_between_tweets, num_of_set, break_time,pix_path_2000)
        i += 1
        if(Twitter_scrapper.tweets_number >= num_of_all_tweets):
            Twitter_scrapper.tweets_number = 0
            break
    time.sleep(60)            