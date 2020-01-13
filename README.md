# atcoder-autocheck
[AtCoder] コードのコンパイル，サンプルケースとの整合性チェック，提出を自動化するツール

## 使う前に
PythonでSeleniumを使ってChromeを動かせる状態にする必要がある．その方法は下記リンクなどを参照:

* [Python + Selenium で Chrome の自動操作を一通り - Qiita](https://qiita.com/memakura/items/20a02161fa7e18d8a693)

## 必要なライブラリ

* Selenium

```
pip install selenium
```

* Beautiful Soup

```
pip install beautifulsoup4
```

## 使い方

#### 1.
`atcoder-autocheck`ディレクトリに`main.cpp`を作成し，そこにコードを書く．
(コンパイルするコードへのパスは`atcoder-autocheck.py`内の`CPP_PATH`(22行目)を変更することに可能)

#### 2.
`autocheck_config.json`を編集し，コンテスト名と
AtCoderのユーザ名・パスワード(自動提出を有効化する場合)を入力する．

コンテスト名はコンテストページのURLに記載されるのと同じものを入力(下を参照)

* `https://atcoder.jp/contests/abc150` -> `abc150`
* `https://atcoder.jp/contests/dwacon6th-prelims` -> `dwacon6th-prelims`

#### 3.
次のコマンドを実行する．

```
python atcoder-autocheck.py [--submit] PROBLEM
```

* `PROBLEM`: 問題名 例) `a`
* `--submit, -s`: 自動提出を有効にする．提出はすべてサンプルケースについて出力がサンプルと一致したときのみ行われる．

## 実行例

* サンプルケースでACのとき

```
$ python atcoder-autocheck.py -s a

=== AtCoder Auto Checker ===
Conteset: abc150
Problem: a
Code: ./main.cpp

Compiling... 
done.
----------------------------------------------
test 1: AC!
----------------------------------------------
test 2: AC!
----------------------------------------------
test 3: AC!
----------------------------------------------
<< AC!! >>
Submitting...
done.
root@a2f0a2022d70:/workspaces/kyopro# 
```

* サンプルケースでWAのとき

```
$ python atcoder-autocheck.py -s a

=== AtCoder Auto Checker ===
Conteset: abc150
Problem: a
Code: ./main.cpp

Compiling... 
done.
----------------------------------------------
test 1: AC!
----------------------------------------------
test 2: WA...
input:
1 501

sample:
No

your answer:
Yes

----------------------------------------------
test 3: AC!
----------------------------------------------
<< Try again... >>
Submitting canceled.
```
