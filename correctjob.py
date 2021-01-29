#!/usr/bin/python
# -*- coding: UTF-8 -*-
import requests
import json
import random
import time


class bcolors:
    # print(bcolors.HEADER + "警告的颜色字体" +bcolors.ENDC)
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class CorrectJob(object):
    """
    批改流程： 先获取所有待批改作业。再模拟逐个点击提交按钮。
    """

    def __init__(self):

        self.sleep_time = random.uniform(1.3, 3.6)
        # 每次提交批改请求的间隔， 最低5秒。
        self.sleep_time_gai = random.uniform(6, 9)
        self.url = None
        self.params = None
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            # "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            # Content-Length: 14
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": "ASP.NET_SessionId=zjiiqbd0tzimiuohec1twbdd; Himall-EmployeeManager=c04veXhHWE5aNUpmUWM5a1hmNTRQcFJiV1htY3czaW5EQmJsTVVKVjFMS3FBelZiVW05dDkvNm84aFZSWUdtbmw2VW1kRzF1OE8ybVpIeHFvRDBwRGc9PQ==; Himall-PlatformManager=c04veXhHWE5aNUpmUWM5a1hmNTRQcFJiV1htY3czaW5EQmJsTVVKVjFMSkpFRWFvclNCVEs4dFNKeUJDc2hkQ3QyaFVOaUJUUXBHZ21iOXM1ZkhIL2c9PQ==",
            "Host": "www.galayun.com",
            "Origin": "https://www.galayun.com",
            # "Referer": "https://www.galayun.com/Admin/AssignWork/Index",
            # Sec-Fetch-Dest: empty
            # Sec-Fetch-Mode: cors
            # Sec-Fetch-Site: same-origin
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75",
            "X-Requested-With": "XMLHttpRequest"
        }

    # 请求url，返回响应文本
    def send_req(self, url, params):
        try:
            res = requests.post(url, params=params, headers=self.headers)
        except Exception as err:
            # print('失败url: ' + url)
            print(err)
            return None
        return res.text

    # 返回ChapterId、QuestionId和Info等信息，用来获取答案列表。
    def get_qid(self):
        question_list = []

        chapters_url = 'https://www.galayun.com/Admin/AssignWork/IndexList'
        chapters_params = {
            "page": "1",
            "rows": "200"
        }

        # 查看所有待批改作业。
        print("正在获取所有待批改作业.....")
        chapters_res = self.send_req(url=chapters_url, params=chapters_params)
        if not chapters_res:
            print(bcolors.BOLD + bcolors.FAIL + '获取待批改作业失败。退出程序。' + bcolors.ENDC)
            exit(1)
        chapters = json.loads(chapters_res)['rows']

        # 根据每个待批改作业，获取待批改题目
        for chapter in chapters:

            question_url = 'https://www.galayun.com/Admin/AssignWork/CorrectIndexList'
            question_params = {
                "Id": chapter['Id'],
                "page": 1,
                "rows": 200
            }

            # 获取某章待批改作业所有题目。
            question_res = self.send_req(url=question_url, params=question_params)
            if not question_res:
                print('获取章节 %s 题目失败。跳过。' + chapter['ChapterName'])
                continue
            questions = json.loads(question_res)["rows"]

            # 遍历题目，获取所有待批改作业信息。
            for Question in questions:
                # print(Question)
                resp = {
                    # 章节ID，用于获取答案
                    "Id": chapter["Id"],
                    # 问题ID，用于获取答案
                    "Qid": Question["QuestionId"],
                    # 班级
                    "ClassId": chapter["ClassId"],
                    # 科目
                    "Subject": chapter["Subject"],
                    # 章节编号
                    "ChapterId": chapter["ChapterId"],
                    # 作业题目
                    "Title": Question["Title"],
                    # 提交情况
                    "Count": Question["Count"]
                }
                question_list.append(resp)

            # 随机休眠一会
            time.sleep(self.sleep_time)

        print("共获取 %d 条待批改作业。" % len(question_list))
        return question_list

    def run(self):

        question_list = self.get_qid()

        # 逐个批改题目。
        for question in question_list:
            try:
                # 哪个班级哪个科目哪个章节哪个题目，未提交x人
                print((bcolors.UNDERLINE + bcolors.BOLD + "批改： [%s] [%s] %s [%s] ，%s 人未提交。" + bcolors.ENDC) %
                      (question["ClassId"], question["Subject"], question["ChapterId"], question["Title"],
                       question["Count"]))

                answers_url = 'https://www.galayun.com/Admin/WorkAnswer/list'
                answers_params = {
                    "Id": question["Id"],  # AssignId
                    "Qid": question["Qid"],
                    'StudentScore': '',
                    'TeacherScore': '',  # TeacherScore 为1 表示未批改的。
                    'page': '1',
                    'rows': '200'
                }

                # 获取所有学生答案
                answers_res = self.send_req(url=answers_url, params=answers_params)
                if not answers_res:
                    print("获取题目答案失败。跳过。")
                    continue
                answers = json.loads(answers_res)["rows"]

                # 批改单个答案
                for answer in answers:

                    # 判断是否已经批改完成。
                    if answer["Score"] >= 10:
                        print("%s 的题目已批改，得分是: %d。跳过。" % (answer["StudentName"], answer["Score"]))
                        continue

                    # 判断得分
                    score = self.set_score(student_answer=answer["StudentAnswer"], image_array=answer["ImageArray"])
                    if not score:
                        print("无法判断 %s 得分。跳过。" % answer["StudentName"])
                        continue

                    # 批改
                    res = self.send_score(answer_id=answer["Id"], score=score, assign_id=question["Id"])
                    if res:
                        print("批改 %s 作业成功，得分是：%s" % (answer["StudentName"], score))
                    else:
                        print("批改 %s 作业失败。" % answer["StudentName"])
                        continue

                    # 至少休眠5秒钟
                    time.sleep(self.sleep_time_gai)

            except Exception as err:
                print(bcolors.FAIL + bcolors.BOLD + "批改作业时出现错误，以下为错误信息:" + bcolors.ENDC)
                print(err)
                exit(1)

        # 提醒手动完成批改。
        print(bcolors.WARNING + bcolors.BOLD + "程序运行结束，您需要登录作业系统查看结果，并手动点击 [完成批改] 按钮。" + bcolors.ENDC)

    # 根据答案文字长度或图片数量给分。
    @staticmethod
    def set_score(student_answer, image_array):

        if len(student_answer) > 30 or len(image_array) > 4:
            return 90
        if len(student_answer) > 15 or len(image_array) > 0:
            return 80
        return 60
        # if len(student_answer) > 10 or len(image_array) > 0:
        #     return 70
        #
        # if len(student_answer) > 3 or len(image_array) > 0:
        #     return 60

        # return random.choice([20, 30, 40, 50])

    # 批改单人单项作业。
    def send_score(self, answer_id, score, assign_id):
        try:
            pi_gai_url = 'https://www.galayun.com/Admin/WorkAnswer/PiGai'
            pi_gai_params = {
                "Id": answer_id,
                "Review": "暂无",  # 评语
                "Score": score,
                "AssignId": assign_id
            }

            # 提交批改请求。
            response = self.send_req(url=pi_gai_url, params=pi_gai_params)
            if not response:
                print("提交批改结果失败。")
                return False

            # 判断是否批改成功
            res = json.loads(response)["success"]
            if res:
                return True

        except Exception as err:
            print(err)
            return False


if __name__ == '__main__':
    a = CorrectJob()
    a.run()
