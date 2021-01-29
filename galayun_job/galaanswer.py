# coding:utf-8
import pandas as pd
import requests
import json


class Answer(object):
    '''
    https://www.galayun.com/Admin/Schedule/Add
    登录后在这个站点“新增排课”，拿到 AliasId: 87 year: 2017
    '''

    def __init__(self, alias_id, year, file_path):
        self.__alias_id = alias_id
        self.__year = year
        # 导出的文件名
        self.__file_path = file_path
        # 课程信息DataFrame
        self.__df_subjects = pd.DataFrame()
        # 章节信息DataFrame
        self.__df_chapters = pd.DataFrame()
        # 选择题DataFrame
        self.__df_objs = pd.DataFrame()
        # 简答题DataFrame
        self.__df_subs = pd.DataFrame()
        # 课程ID
        self.__subjects_id_list = []
        # 章节ID
        self.__chapters_id_list = []
        # 公共头部
        self.__headers = {
            "Cookie": "Hm_lvt_79d25534ef220c32240b2249cc47f2d3=1604635528,1604645443; ASP.NET_SessionId=0kugsvnsdkpkwnq31fgpuws0; Himall-EmployeeManager=c04veXhHWE5aNUpmUWM5a1hmNTRQcFJiV1htY3czaW5EQmJsTVVKVjFMSTFHeU5iZnV1SWdTSkxXKzA3SnFVUzFFWEY2ZjRsZDNxM0NlbE12ZlVldGc9PQ==; Himall-PlatformManager=c04veXhHWE5aNUpmUWM5a1hmNTRQcFJiV1htY3czaW5EQmJsTVVKVjFMSjUvWUdHTzhZMTRRUGVaSjBtTXpDd3YvME1MMUJ3Q2R1Zmd0cW50VUdFdFE9PQ==",
            "Host": 'www.galayun.com',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36 Edg/86.0.622.68",
        }

    # 根据专业id获取该专业的课程。
    def __get_subjects(self):
        get_subjects_url = 'https://www.galayun.com/Admin/Schedule/GetStandSubjects'
        get_subjects_params = {
            'AliasId': self.__alias_id,
            'year': self.__year
        }

        response = requests.post(url=get_subjects_url, headers=self.__headers, params=get_subjects_params)
        # 保存DataFrame格式的课程信息。
        self.__df_subjects = pd.read_json(response.content.decode())
        if self.__df_subjects.empty:
            print('%s %s专业内课程为空。' % (self.__year, self.__alias_id))
            exit(1)
        # 保存专业内课程列表
        self.__subjects_id_list = self.__df_subjects['SubjectId'].values.tolist()
        # print('本专业共发现：%d 门课程' % len(self.__subjects_id_list))

    # 根据课程id，获取该课程的章节id等信息。
    def __get_chapters(self):
        if not self.__subjects_id_list:
            self.__get_subjects()
        url = 'https://www.galayun.com/Admin/StandResourceRight/SubjectTeacherManagmentList'
        # 章节df列表
        chapter_df_list = []
        for subject_id in self.__subjects_id_list:
            params = {
                'SubjectId': subject_id,
                'page': '1',
                'rows': '900'
            }
            response = requests.post(url=url, headers=self.__headers, params=params)
            df_tmp = pd.DataFrame(json.loads(response.content.decode())['rows'])
            if df_tmp.empty:
                print('Chapter %s is null,skip...' % subject_id)
                continue
            # 去掉章节重复值。附加到章节id列表
            df_tmp1 = df_tmp.drop_duplicates('ChapterId')
            self.__chapters_id_list += (df_tmp1['ChapterId'].values.tolist())
            # 添加新列
            df_tmp.insert(0, column='SubjectId', value=subject_id)
            # dataframe追加到列表
            chapter_df_list.append(df_tmp)
        # 将列表中的Dataframe合并
        self.__df_chapters = pd.concat(chapter_df_list, axis=0)

    # todo 获取答案
    def __get_answer(self):
        if not self.__chapters_id_list:
            self.__get_chapters()
        # 选择题和简单题DataFrame列表
        df_objs_list = []
        df_subs_list = []

        for chapter_id in self.__chapters_id_list:
            print('正在处理处理%s章节' % chapter_id)
            url = 'https://www.galayun.com/Admin/AssignWork/AnswerDetail'
            params = {
                'ChapterId': chapter_id
            }
            # 获取http响应
            response = requests.post(url=url, headers=self.__headers, params=params)
            # 获取的响应转为DataFrame数据。
            df_objs = pd.DataFrame(json.loads(response.content.decode())['objs'])
            df_subs = pd.DataFrame(json.loads(response.content.decode())['subs'])

            if not df_objs.empty:
                # 插入章节ID列
                df_objs.insert(0, column='ChapterID', value=chapter_id)
                # dataframe追加到列表
                df_objs_list.append(df_objs)
            if not df_subs.empty:
                # 插入章节ID列
                df_subs.insert(0, column='ChapterID', value=chapter_id)
                # dataframe追加到列表
                df_subs_list.append(df_subs)

            if df_subs.empty and df_objs.empty:
                print('chapter %s objs and subs is null,skip...' % chapter_id)
                continue

        # 将列表中的Dataframe合并
        self.__df_objs = pd.concat(df_objs_list, axis=0)
        self.__df_subs = pd.concat(df_subs_list, axis=0)


    # 返回章节列表
    def get_chapters_id(self):
        if not self.__chapters_id_list:
            self.__get_chapters()
        return self.__chapters_id_list

    # 返回课程列表
    def get_objects_id(self):
        if not self.__subjects_id_list:
            self.__get_subjects()
        return self.__subjects_id_list

    def to_file(self):
        # if not self.__chapters_id_list:
        #     self.__get_chapters()
        self.__get_answer()
        subjects_sheet_name = str(self.__year) + str(self.__alias_id) + '课程'
        chapters_sheet_name = str(self.__year) + str(self.__alias_id) + '章节'
        objs_sheet_name = str(self.__year) + str(self.__alias_id) + '选择题'
        subs_sheet_name = str(self.__year) + str(self.__alias_id) + '问答题'
        # 将Dataframe写入到excel文件。
        with pd.ExcelWriter(self.__file_path) as writer:
            self.__df_chapters.to_excel(writer, sheet_name=chapters_sheet_name)
            self.__df_subjects.to_excel(writer, sheet_name=subjects_sheet_name)
            self.__df_objs.to_excel(writer, sheet_name=objs_sheet_name)
            self.__df_subs.to_excel(writer, sheet_name=subs_sheet_name)
        return 'Save to  %s success.' % self.__file_path

    # def answer_to_file(self):
    #     self.__get_answer()
    #     objs_sheet_name = str(self.__year) + str(self.__alias_id) + '选择题'
    #     subs_sheet_name = str(self.__year) + str(self.__alias_id) + '问答题'
    #     # 将Dataframe写入到excel文件。
    #     with pd.ExcelWriter(self.__file_path, engine='xlsxwriter') as writer:
    #         self.__df_objs.to_excel(writer, sheet_name=objs_sheet_name)
    #         self.__df_subs.to_excel(writer, sheet_name=subs_sheet_name)
    #     return 'Save to  %s success.' % self.__file_path


if __name__ == '__main__':
    # wang_an_2019 = Answer(87, 2020, r'chapters2020wa-1.xlsx')
    # wang_an_2019.chapters_to_file()
    # print(wang_an_2019.get_chapters_id())
    # print(wang_an_2019.get_chapters_id())
    # print(wang_an_2019.get_objects_id())
    # print(wang_an_2019.to_file())
    # ui2019 = Answer(89, 2019, r'chapters2019ui.xlsx')
    # ui2019.to_file()
    # waw2019 = Answer(457, 2019, r'chapterswaw2019.xlsx')
    # waw2019.to_file()
    waw2020 = Answer(457, 2020, r'chapterswaw2020.xlsx')
    waw2020.to_file()

