import json
import os
import re
import urllib.request
import sys

from datetime import datetime , timedelta
from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = 'xoxp-503049869125-504578722048-506894891009-770061cc169180c2533b15c7eef6e25a'
slack_client_id = '503049869125.506759767824'
slack_client_secret = 'fd7718b16d6eeb80abc281a2e1bb3db8'
slack_verification = '2q4ynAigKVeeiqrFjLLfXlvD'
sc = SlackClient(slack_token)
# kredit job

# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    date = datetime.today().strftime("%Y-%m-%d")
    compile_text = re.compile(r'\d\d\d\d-\d\d-\d\d')
    tmp_lst = []
    tmp_lst = compile_text.findall(text)
    # 텍스트가 입력이 없다면 오늘 메뉴 출력
    if len(text) == 12:
        url = "http://welfoodstory.azurewebsites.net/?category=2%EC%BA%A0%ED%8D%BC%EC%8A%A4-3&date=" + date

    else:
        if tmp_lst == [] or len(tmp_lst) > 1:
            foods = ['다음과같은 형식으로 입력해주세요!!', 'YYYY-MM-DD']
            foods.append('input text: ' + text[13:24])

            return u'\n'.join(foods)

        today_year = int(date[0:4])
        today_month = int(date[5:7])
        today_day = int(date[8:10])
        ip_year = int(tmp_lst[0][0:4])
        ip_month = int(tmp_lst[0][5:7])
        ip_day = int(tmp_lst[0][8:10])

        if abs(today_year - ip_year) > 1 or abs(
                today_month - ip_month) > 1 or today_day - ip_day < -2 or today_day - ip_day > 1:
            foods = ['당일날짜 기준 하루전과 이틀뒤까지만 조회 가능합니다!!', 'YYYY-MM-DD']
            foods.append('input text: ' + text[13:24])

            return u'\n'.join(foods)

        url = "http://welfoodstory.azurewebsites.net/?category=2%EC%BA%A0%ED%8D%BC%EC%8A%A4-3&date=" + tmp_lst[0]

    # URL 주소에 있는 HTML 코드를 soup에 저장
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

    foods = []

    for source_code in soup.find_all("div", class_="menu-item"):
        menu_title = source_code.find("div", class_="menu-item-title").get_text()

        if "셰프" in menu_title:
            menu_list = source_code.find("div", class_="menu-item-contents").get_text()
            # foods.append(menu_list)
            foods.append('=============\n' + menu_title + '\n' + menu_list)
            # print("========")
            # print(menu_title)
            # print(menu_list)
            # print("========")

    foods = foods[2:5]
    # foods.insert(0, date + "의 점심")
    if len(text) == 12:
        foods.insert(0, date + "의 점심")
    else:
        foods.insert(0, text[13:24] + "의 점심")

    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(foods)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_naver_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)
    # if slack_event['event_time'] < (datetime.now() - timedelta(seconds=1)).timestamp():
    #     return make_response("this message is before sent.", 200, {"X-Slack-No-Retry": 1})
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)