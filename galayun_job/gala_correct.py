# coding:utf-8
import requests
import json
import random
import time


class Ga_job(object):

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.47',
            'Cookie': 'Hm_lvt_79d25534ef220c32240b2249cc47f2d3=1604635528,1604645443; ASP.NET_SessionId=t4rszyeja10zdrccbmvhutbe; Himall-EmployeeManager=c04veXhHWE5aNUpmUWM5a1hmNTRQcFJiV1htY3czaW5EQmJsTVVKVjFMTGR3clpTbThzZUdIWmZxU1Y0VjhoUXlRVzU4djEwVmpRQXQ4ajg5b1h1clE9PQ==; Himall-PlatformManager=c04veXhHWE5aNUpmUWM5a1hmNTRQcFJiV1htY3czaW5EQmJsTVVKVjFMSXhHa09zck02Z1Y4alFqTm1vZlNhNE1FSDdxSXN5T29DSjBDQ3lZcmFTdWc9PQ==',
            'Host': 'www.galayun.com'
        }
        # 批改评语及随机分数。
        self.review = ['这让我怎么改', '应付', '精炼', '好', '可以', '不错']
        self.score = ['0', str(random.randint(60, 68)), str(random.randint(63, 75)), str(random.randint(70, 81)),
                      str(random.randint(75, 89)), str(random.randint(83, 100))]

    # 根据答案长度，生成评语和分数
    def score(self, num):
        pass

    # 拿到所有作业，返回 job_id "Id" list
    def get_all_job_id(self):
        url = 'https://www.galayun.com/Admin/AssignWork/IndexList'
        params = {
            'page': '1',
            'rows': '500'
        }
        try:
            # 直接返回作业列表list。
            res = requests.post(url=url, headers=self.headers, params=params)
            job_list = json.loads(res.content.decode())['rows']
            return job_list
        except Exception:
            print('get jobs error, exit.')
            exit(1)

    # 执行程序
    def run(self):
        # 获取所有布置的作业。
        jobs_list = self.get_all_job_id()
        if len(jobs_list) == 0:
            print('暂无需要批改的作业。')
            exit(0)
        url = 'https://www.galayun.com/Admin/AssignWork/CorrectIndexList'
        for job in jobs_list:
            try:
                job_id = job['Id']
                params = {
                    'Id': str(job_id),
                    'page': '1',
                    'rows': '50'
                }

                # 获取作业的题目列表
                response = requests.post(url=url, headers=self.headers, params=params)
                question_list = json.loads(response.content.decode())['rows']

                # 如果没拿到题目列表，跳过。
                if len(question_list) == 0:
                    print('skip job %s.' % job_id)
                    continue
                else:
                    print(r'id:%s，正在处理:《%s》-> “%s”' % (job_id, job['Subject'], job['ChapterName']))

                # 批改单次题目所有学生作业
                for question in question_list:

                    question_id = question['QuestionId']
                    # 拿到单次题目的所有答案
                    answer_ids = self.get_answer_list(job_id, question_id)
                    # 如果没拿到题目列表，跳过。
                    if len(answer_ids) == 0:
                        print('skip question %s.' % question_id)
                        continue
                    else:
                        print(r'批改：%s' % question['Title'])

                    # 遍历本题所有学生答案并批改作业。
                    for answer_id in answer_ids:
                        # 批改单个学生的单个题目
                        response = self.pi_gai(answer_id, job_id)
                        if not response:
                            print('correct %s error.' % answer_id)

                # 所有学生作业批改万抽，完成批改。
                res = self.finish_job(job_id)
                if res:
                    print(r'”%s“ 批改完成. ^_^' % (job['ChapterName']))

            except Exception:
                print('run  %s job error.' % job['Id'])
                continue

    # 完成作业批改
    def finish_job(self, job_id):
        try:
            url = 'https://www.galayun.com/Admin/AssignWork/PiGaiFinish'
            params = {
                'AssignId': str(job_id)
            }
            response = requests.post(url=url, headers=self.headers, params=params)
            res = json.loads(response.content.decode())
            # da = '{"success":true,"msg":"本次批改完成"}'
            if res["success"]:
                return True
        except Exception:
            return False

    # 拿到单次作业内单个问题所有学生答案， 返回 单个答案ID list
    def get_answer_list(self, job_id, question_id):
        url = 'https://www.galayun.com/Admin/WorkAnswer/list'
        try:
            params = {
                'Id': str(job_id),
                'Qid': str(question_id),
                'StudentScore': '',
                # TeacherScore 为1 表示未批改的。
                'TeacherScore': '1',
                'page': '1',
                'rows': '80'
            }
            response = requests.post(url=url, headers=self.headers, params=params)
            answer_ids = []
            res = json.loads(response.content.decode())['rows']
            for answer in res:
                answer_ids.append(answer["Id"])
            return answer_ids
        except Exception:
            return 0

    # 查看单个问题学生答案， 返回 StudentText 长度
    def get_stu_answer_len(self, answer_id):
        url = 'https://www.galayun.com/Admin/WorkAnswer/GetAnswer'
        try:
            params = {
                'Id': str(answer_id)
            }
            response = requests.post(url=url, headers=self.headers, params=params)
            res = json.loads(response.content.decode())['StudentText']
            return len(res)
        except Exception:
            return 0

    # 单次批改作业，  根据长度批改作业。
    # answer_id 单个答案ID
    # job_id 本次布置的作业ID
    def pi_gai(self, answer_id, job_id):
        try:
            answer_len = self.get_stu_answer_len(answer_id)
            url = 'https://www.galayun.com/Admin/WorkAnswer/PiGai'
            # 根据答案长度，给定评语和分数。
            if answer_len <= 2:
                review = self.review[0]
                score = self.score[0]
            elif answer_len <= 5:
                review = self.review[1]
                score = self.score[1]
            elif answer_len <= 10:
                review = self.review[2]
                score = self.score[2]
            elif answer_len <= 20:
                review = self.review[3]
                score = self.score[3]
            elif answer_len <= 50:
                review = self.review[4]
                score = self.score[4]
            elif answer_len >= 51:
                review = self.review[5]
                score = self.score[5]
            else:
                review = '难为人了啊'
                score = '0'
            # 批改单次作业。
            params = {
                'Id': str(answer_id),
                'Review': review,
                'Score': score,
                'AssignId': str(job_id)
            }
            response = requests.post(url=url, params=params, headers=self.headers)
            res = json.loads(response.content.decode())
            # {"success":true,"finish":true}
            if res['success'] and res['finish']:
                # 随机休眠一会。
                time.sleep(random.uniform(0.5, 1.3))
                return True
        except Exception:
            time.sleep(random.uniform(0.5, 1.5))
            return False


if __name__ == '__main__':
    xu = Ga_job()
    xu.run()
