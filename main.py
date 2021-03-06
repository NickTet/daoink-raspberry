#!/usr/bin/env python
#coding:utf-8
"""
file:.py
date:2018/10/15 16:40
author:    peak
description:
"""

from config import engine, Session, Printer_Name
from model import Base, Order
import datetime, time, requests, subprocess, os, commands




def Query():
    # 查询排队方式为自动排队的订单
    Base.metadata.create_all(engine)
    session = Session()
    All_Order = session.query(Order).filter(Order.Time_Way == 1).all()
    if All_Order:
        for i in range(len(All_Order)):
            if All_Order[i].Print_Status == 1:
                # 尝试下载订单中的文件
                try:
                    url = "http://rooins.careyou.xin/static/Upload_Files/"+All_Order[i].File_Dir
                    r = requests.get(url)
                    if r.status_code != 200:            # 判断url若不是200，则记录错误到日志
                        raise IOError('{} {} {}' .format(r.status_code, r.reason, r.url))
                    else:
                        with open('./User_Files/To_Print/'+All_Order[i].File_Dir, 'wb') as f:
                            f.write(r.content)
                except Exception as e:
                    # 将错误写入下载错误日志
                    with open('./log/download_error_log', 'a') as f:
                        f.write(str(datetime.datetime.now()) + " " + All_Order[i].File_Dir + " " + str(e) + "\n")
                else:
                    # 将下载成功写入下载成功日志
                    with open("./log/download_log", "a") as f:
                        f.write(str(datetime.datetime.now()) + " " + All_Order[i].File_Dir + " " + "success-download" + "\n")
                    # 在数据库中做出标记，文件已下载成功
                    All_Order[i].Print_Status = 2
                finally:
                    session.commit()

def Print():

    Base.metadata.create_all(engine)
    session2 = Session()
    # 将 ./User_Files/To_Print/ 中的文件名导入到预打印日志中
    cmd = "ls -t ./User_Files/To_Print/ > ./log/ToPrint_filename"
    subprocess.call(cmd, shell=True)
    ToPrint = open("./log/ToPrint_filename", 'r+')
    direction_option = ""     # 打印方向参数
    for line in ToPrint:
        printed_order = session2.query(Order).filter(Order.File_Dir == line[:-1])  # 查询当前打印订单对象
        if printed_order.Print_Direction == 2:
            direction_option = "-o landscape"
        try:
            # 开始尝试打印
            print_cmd = 'lp -d {} -n {} -o fitplot {} ./User_Files/To_Print/{}' .format(Printer_Name, printed_order.Print_Copies, direction_option, line[:-1])
            returnCode = subprocess.call(print_cmd, shell=True)
            if returnCode != 0:
                error = commands.getoutput(print_cmd)
                raise IOError(error)
        except Exception as e:
            # 捕获错误，并将错误写入错误日志中
            with open('./log/print_error_log', 'a') as f:
                f.write(str(datetime.datetime.now()) + " " + line[:-1] + " " + str(e) + "\n")
        else:
            # 将打印成功的文件移动到 ./User_Files/Finished_Print 这个目录中
            subprocess.call('mv ./User_Files/To_Print/{} ./User_Files/Finished_Print/' .format(line[:-1]), shell=True)

            # 在数据库中修改打印状态为3，表示已经打印

            printed_order.Print_Status = 3
            session2.commit()
            # session2.close()

            # 在./log/print_access_log 中写入打印成功日志
            with open('./log/print_access_log', 'a') as f:
                f.write(str(datetime.datetime.now()) + " " + line[:-1] + " " + "Successfully-Added-To-Printer")

while 1:
    Query()
    time.sleep(5)
    Print()





