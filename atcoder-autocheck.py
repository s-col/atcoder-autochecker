import sys
import os
import re
import time
import json
import subprocess
from typing import List, Tuple
from urllib import request
from argparse import ArgumentParser

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup


CONFIG_PATH = "./autocheck_config.json"  # 設定ファイルへのパス
CPP_PATH = "./main.cpp"  # C++ファイルへのパス

COMPILING_CMD = ["g++", "-ggdb", "-Wall", "-std=gnu++14"]


def get_args():
    parser = ArgumentParser()
    parser.add_argument("problem", type=str,
                        help="Problem's name.  ex) a")
    parser.add_argument("--submit", "-s", action="store_true",
                        help="Enable auto submission.")
    return parser.parse_args()


class AtCoderAutoChecker:
    """
    AtCoderAutoChecker
        contest: コンテスト名 (ex: abc123)
        problem: 問題名 (ex: c)
        code: コードへのパス
    """

    __slots__ = ("contest", "problem", "code",
                 "inSmpls", "outSmpls", "is_compiled", "driver", "is_logged_in")

    def __init__(self, contest: str, problem: str):
        self.contest = contest.lower()
        self.problem = problem.lower()
        self.code = None  # type: str
        self.inSmpls = None  # type: List[str]
        self.outSmpls = None  # type: List[str]
        self.is_compiled = False
        self.is_logged_in = False
        self.driver = None  # type: "Webdriver"

        # chrome driverを立ち上げる
        self._boot_chrome_driver()

        # サンプルをフェッチ
        try:
            self.fetch_samples()
        except Exception as e:
            self.driver.close()
            raise e

    def _boot_chrome_driver(self):
        options = Options()
        options.headless = True
        options.add_argument("--no-sandbox")  # これが無いとエラーになる
        self.driver = webdriver.Chrome(options=options)

    def set_code(self, code: str):
        self.code = code
        self.is_compiled = False

    def chrome_quit(self):
        self.driver.quit()

    def chrome_close(self):
        self.driver.close()

    def fetch_samples(self):
        """
        入出力サンプルを取得する
        """
        # 問題ページのURL
        url = "https://atcoder.jp/contests/{0:s}/tasks/{0:s}_{1:s}".format(
            self.contest, self.problem)

        self.driver.get(url)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_all_elements_located)
        html = self.driver.page_source.encode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        self.inSmpls = []
        self.outSmpls = []

        idx = 0
        while True:
            selector = r".lang-ja #pre-sample{:d}".format(idx)
            smpl = soup.select_one(selector)
            if not smpl:
                break
            if idx % 2 == 0:
                self.inSmpls.append(smpl.text)
            else:
                self.outSmpls.append(smpl.text)
            idx += 1

        assert self.inSmpls and self.outSmpls, "Sample case not found."

    def compile(self):
        """
        C++をコンパイルする
        """
        print("Compiling... ")
        cmd = [*COMPILING_CMD, self.code]
        result = subprocess.run(cmd, capture_output=True)
        if result.stdout:
            print(result.stdout.decode())
        if result.stderr:
            print(result.stderr.decode())
        assert result.returncode == 0, "Compile failed."
        print("done.")
        self.is_compiled = True

    def test(self) -> bool:
        """
        サンプルとの整合性をチェックする
        すべてACならTrueを返す
        """
        assert self.is_compiled == True, "Your code hasn't been compiled yet!"

        all_ac = True

        for i in range(len(self.inSmpls)):
            process = subprocess.Popen(
                "./a.out", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding="utf-8")

            out, _ = process.communicate(self.inSmpls[i], timeout=6)

            print("----------------------------------------------")
            if out == self.outSmpls[i]:
                print("test {:d}: AC!".format(i + 1))
            else:
                print("test {:d}: WA...".format(i + 1))
                print("input:")
                print(self.inSmpls[i])
                print("sample:")
                print(self.outSmpls[i])
                print("your answer:")
                print(out)
                all_ac = False

        print("----------------------------------------------")
        if all_ac:
            print("<< AC!! >>")
        else:
            print("<< Try again... >>")

        return all_ac

    def submit(self, id_: str, password: str):
        # loginしてないならする
        if not self.is_logged_in:
            self.login(id_, password)

        # 提出ページのURL
        url = "https://atcoder.jp/contests/{0:s}/submit?taskScreenName={0:s}_{1:s}".format(
            self.contest, self.problem)

        self.driver.get(url)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_all_elements_located)

        # エディタ変更のボタンを押す
        editer_button = self.driver.find_element_by_css_selector(
            r"button.btn-toggle-editor")
        editer_button.click()

        # エディタにコードを入力
        # editer = self.driver.find_element_by_css_selector(
        #     r"#sourceCode > textarea")
        # with open(self.code, "r", encoding="utf-8") as f:
        #     editer.send_keys(f.read())

        # send_keysはとても遅いので，excecute_scriptで代替する
        # 参考: https://srbrnote.work/archives/3025
        with open(self.code, "r", encoding="utf-8") as f:
            src = f.read()
            # 以下はjavascriptがバグらないための変換
            src = repr(src).strip("\'")
            src = src.replace("\"", "\\\"").replace("\'", "\\\'")
            self.driver.execute_script(
                'document.querySelector("#sourceCode > textarea").value="{:s}";'.format(
                    src)
            )

        # 提出ボタンを押す
        submit_botton = self.driver.find_element_by_id("submit")
        submit_botton.click()

        # 提出できたかを確認する
        # 提出ページに遷移していなかったらおそらくできていないだろう
        assert self.driver.current_url == "https://atcoder.jp/contests/{:s}/submissions/me".format(
            self.contest), "Submission failed."

    def login(self, id_: str, password: str):
        assert not self.is_logged_in

        url = "https://atcoder.jp/login"

        self.driver.get(url)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_all_elements_located)

        # username_form = self.driver.find_element_by_id("username")
        # username_form.send_keys(id_)
        self.driver.execute_script(
            'document.getElementById("username").value="{:s}";'.format(id_)
        )
        # password_form = self.driver.find_element_by_id("password")
        # password_form.send_keys(password)
        self.driver.execute_script(
            'document.getElementById("password").value="{:s}";'.format(
                password)
        )
        login_button = self.driver.find_element_by_id("submit")
        login_button.click()

        # loginできなかった場合はloginページに戻されるから，これを検知することでloginの成否を検出する
        assert not re.search(r"https://atcoder.jp/login*",
                             self.driver.current_url), "Login failed."

        self.is_logged_in = True

    def auto(self, code: str, submission: bool = False, id_: str = None, password: str = None):
        try:
            print()
            print("=== AtCoder Auto Checker ===")
            print("Conteset: {:s}\nProblem: {:s}\nCode: {:s}".format(
                contest, problem, code))
            print()

            self.set_code(code)
            self.compile()
            is_ac = self.test()
            if submission:
                if is_ac:
                    assert id_ and password
                    print("Submitting...")
                    self.submit(id_, password)
                    print("done.")
                else:
                    print("Submitting canceled.")
        except Exception as e:
            self.chrome_close()
            raise e
        else:
            self.chrome_close()


if __name__ == "__main__":
    args = get_args()

    problem = args.problem
    submission_flag = args.submit

    # 設定の読み込み
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    contest = config["contest"].lower()

    id_ = None
    password = None
    if submission_flag:
        id_ = config["Account"]["id"]
        password = config["Account"]["password"]

    autoChecker = AtCoderAutoChecker(contest, problem)
    autoChecker.auto(CPP_PATH, submission_flag, id_, password)
