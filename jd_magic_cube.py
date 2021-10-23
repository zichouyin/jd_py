#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/10/15 2:23 下午
# @File    : jd_magic_cube.py
# @Project : scripts
# @Cron    : 37 5,22 * * *
# @Desc    : 京东首页->新品首发->魔方
import asyncio
import json
import urllib.parse

import aiohttp

from config import USER_AGENT
from utils.process import process_start
from utils.logger import logger
from utils.console import println
from utils.jd_init import jd_init


@jd_init
class JdMagicCube:
    """
    京东秒杀-秒秒币
    """

    headers = {
        'user-agent': USER_AGENT,
        'content-type': 'application/x-www-form-urlencoded',
        'referer': 'https://h5.m.jd.com/babelDiy/Zeus/2NUvze9e1uWf4amBhe1AV6ynmSuH/index.html',
        'origin': 'https://h5.m.jd.com',
    }

    encrypt_project_id = None

    source_code = 'wh5'

    async def request(self, session, params, method='POST'):
        """
        请求数据
        :param params:
        :param session:
        :param method:
        :return:
        """
        try:
            url = 'https://api.m.jd.com/client.action?'
            url += urllib.parse.urlencode(params)
            if method == 'POST':
                response = await session.post(url=url)
            else:
                response = await session.get(url=url)

            text = await response.text()

            data = json.loads(text)

            return data

        except Exception as e:
            println('{}, 请求数据失败, {}'.format(self.account, e.args))

    async def exchange(self, session):
        """
        兑换
        :return:
        """
        params = {
            'functionId': 'doInteractiveAssignment',
            'body': {"encryptProjectId": "3pp3mvzmgcFm7mvU3S1wZihNKi1H",
                     "encryptAssignmentId": "2qZXV5kAqBJjkJmYi8C2874WyHxj", "sourceCode": "acexinpin0823", "itemId": "",
                     "actionType": "", "completionFlag": "", "ext": {"exchangeNum": 1}},
            'appid': 'content_ecology',
        }
        res = await self.request(session, params)
        println(res)

    async def get_encrypt_project_id(self, session):
        """
        :return:
        """
        res = await self.request(session, {
            'functionId': 'getInteractionHomeInfo',
            'body': {"sign": "u6vtLQ7ztxgykLEr"},
            'appid': 'content_ecology',
        })

        return res.get('result', dict()).get('taskConfig', dict()).get('projectId', '3WaFbpr4LR1fdhGxqi4Gkg2JirSZ')

    async def get_tasks(self, session):
        """
        :return:
        """

        self.encrypt_project_id = await self.get_encrypt_project_id(session)
        if not self.encrypt_project_id:
            println('{}, 获取活动ID失败!'.format(self.account))

        res = await self.request(session, {
            'functionId': 'queryInteractiveInfo',
            'body': json.dumps({"encryptProjectId": self.encrypt_project_id, "sourceCode": self.source_code}),
            'client': 'wh5',
            'clientVersion': '1.0.0'
        })
        if res.get('code') != '0':
            return None
        return res.get('assignmentList')

    @logger.catch
    async def do_tasks(self, session, task_list):
        """
        做任务
        :param session:
        :param task_list:
        :return:
        """
        for task in task_list:
            task_name = task['assignmentName']
            task_type = task['assignmentType']
            cur_cnt = task.get('completionCnt', 0)  # 子任务完成次数

            times_limit = task['assignmentTimesLimit']  # 总共需要完成的次数
            if cur_cnt >= times_limit:
                println('{}, 任务:《{}》已完成过!'.format(self.account, task_name))
                continue
            if task_type == 1:
                ext = task.get('ext', None)
                if not ext:
                    continue
                extra_type = ext.get('extraType', None)
                if not extra_type:
                    continue
                if not task['ext'][extra_type]:
                    continue
                for i in range(cur_cnt, times_limit):
                    item = task['ext'][extra_type][i]
                    println('{}, 去做任务:《{}》, {}/{}.'.format(self.account, task_name, i + 1, times_limit))
                    body = {
                        'encryptAssignmentId': task['encryptAssignmentId'],
                        'encryptProjectId': self.encrypt_project_id,
                        'itemId': item['itemId'],
                        'actionType': 1,
                        "sourceCode": self.source_code,
                        "completionFlag": "",
                        "ext": {}
                    }
                    params = {
                        'functionId': 'doInteractiveAssignment',
                        'body': json.dumps(body),
                        'client': 'wh5',
                        'clientVersion': '1.0.0'
                    }
                    await self.request(session, params)
                    timeout = ext['waitDuration']
                    println('{}, 等待{}秒后, 去领取任务:《{}》奖励...'.format(self.account, timeout, task_name))
                    await asyncio.sleep(timeout)
                    body['actionType'] = 0
                    params['body'] = json.dumps(body)
                    res = await self.request(session, params)
                    println('{}, {}:{}/{}, {}'.format(self.account, task_name, i + 1, times_limit, res.get('msg')))

            elif task_type == 0:
                for i in range(cur_cnt, times_limit):
                    println('{}, 去做任务:《{}》, {}/{}.'.format(self.account, task_name, i + 1, times_limit))
                    body = {
                        "encryptAssignmentId": task['encryptAssignmentId'],
                        "itemId": "",
                        'encryptProjectId': self.encrypt_project_id,
                        "actionType": 0,
                        "completionFlag": True,
                        "sourceCode": self.source_code,
                        "ext": {}
                    }
                    params = {
                        'functionId': 'doInteractiveAssignment',
                        'body': json.dumps(body),
                        'client': 'wh5',
                        'clientVersion': '1.0.0'
                    }
                    res = await self.request(session, params)
                    println('{}, {}:{}/{},{}'.format(self.account, task_name, i + 1, times_limit, res.get('msg')))
                    await asyncio.sleep(1)
            elif task_type == 3:
                for i in range(cur_cnt, times_limit + 1):
                    body = {
                        "encryptAssignmentId": task['encryptAssignmentId'],
                        "itemId": task['ext'][task['ext']['extraType']][i]['itemId'],
                        "actionType": 0,
                        "completionFlag": "",
                        "sourceCode": self.source_code,
                        "ext": {},
                        'encryptProjectId': self.encrypt_project_id,
                    }
                    params = {
                        'functionId': 'doInteractiveAssignment',
                        'body': json.dumps(body),
                        'client': 'wh5',
                        'clientVersion': '1.0.0'
                    }
                    res = await self.request(session, params)
                    println('{}, {}:{}/{},{}'.format(self.account, task_name, i + 1, times_limit, res.get('msg')))

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            task_list = await self.get_tasks(session)
            if not task_list:
                println('{}, 无法获取任务列表, 退出程序!'.format(self.account))
                return
            await self.do_tasks(session, task_list)
            await self.exchange(session)


if __name__ == '__main__':
    # from config import JD_COOKIES
    # app = JdSecondCoin(**JD_COOKIES[0])
    # asyncio.run(app.run())
    process_start(JdMagicCube, '京东APP-魔方')
