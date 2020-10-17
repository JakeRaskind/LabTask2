import requests
from bs4 import BeautifulSoup
import re


def parse_text(text):
    text = re.sub('[^а-яА-Я]', ' ', text).lower()
    tokens = text.split()
    return tokens


def add_word_to_node(node, word, index):
    #Это слово найдено
    if word == node['word'][0]:
        node['word'][1].append(index)
        return
    # Слово меньше текущего
    if word < node['word'][0]:
        # левого потомка нет
        if node.get('left', {'height': 0}) == {'height': 0}:
            node['left'] = {'word': (word, [index]), 'height': 1}
        # левый потомок есть, идем в него
        else:
            add_word_to_node(node['left'], word, index)
            if node['left']['height'] - 1 > node.get('right', {'height': 1})['height']:
                left_pivot(node)
    # слово больше текущего
    else:
        # правого потомка нет
        if node.get('right', {'height': 0}) == {'height': 0}:
            node['right'] = {'word': (word, [index]), 'height': 1}
        # правый потомок есть
        else:
            add_word_to_node(node['right'], word, index)
            if node['right']['height'] - 1 > node.get('left', {'height': 1})['height']:
                right_pivot(node)
    node['height'] = 1 + max(node.get('left', {'height': 0})['height'], node.get('right', {'height': 0})['height'])


def add_word_to_tree(tree, word, index):
    if tree == {}:
        tree['word'] = (word, [index])
        tree['height'] = 1
        return
    add_word_to_node(tree, word, index)


def left_pivot(node):
    A, B, C = node['left'].get('left', {'height': 0}), node['left'].get('right', {'height': 0}), node.get('right', {'height': 0})
    X, Y = node['word'], node['left']['word']
    node['left'], node['word'] = A, Y
    node['right'] = {'word': X}
    (node['right']['left'], node['right']['right']) = (B, C)
    node['right']['height'] = max(B['height'], C['height'])


def right_pivot(node):
    A, B, C = node.get('left', {'height': 0}), node['right'].get('left', {'height': 0}), node['right'].get('right', {'height': 0})
    X, Y = node['word'], node['right']['word']
    node['right'], node['word'] = C, Y
    node['left'] = {'word': X}
    (node['left']['left'], node['left']['right']) = (A, B)
    node['left']['height'] = max(A['height'], B['height'])


def find_word(node, word):
    cur = node.get('word', False)
    if not cur:
        return cur
    if cur[0] == word:
        return node['word'][1]
    if cur[0] > word:
        return find_word(node.get('left', {}), word)
    if cur[0] < word:
        return find_word(node.get('right', {}), word)


def iterate_main_page(headers):
    news_urls = set()
    url = r'https://xn----dtbbicbpaeospj0cgq.xn--p1ai/category/novosti/'
    session = requests.Session()
    res = session.get(url, headers=headers)
    news_urls |= extract_urls(res)
    # bs = BeautifulSoup(res.text, features='lxml')
    # load_data = {'query': str(bs.find('script', id='query_vars'))[41:-11],
    #              'page': 0,
    #              'part': 'category-posts'}
    # # for i in range(10):
    #     load_data['page'] = i
    #     butch = session.post('https://xn----dtbbicbpaeospj0cgq.xn--p1ai/wp-admin/admin-ajax.php?action=ajaxs_action&ajaxs_nonce=32335cc76c&jxs_act=ajaxs_load_posts', data=load_data)
    #     print(butch.text)
    #     news_urls |= extract_urls(butch)
    # print(len(news_urls))
    return news_urls


def extract_urls(response):
    urls = set()
    bs = BeautifulSoup(response.text, features='lxml')
    for tag in bs.findAll('a', {'class': "posts__item_title-link"}):
        urls.add(tag['href'])
    return urls


def extract_news(news_urls, headers):
    articles = []
    for url in news_urls:
        cur = ['URL: ' + url]
        soup = BeautifulSoup(requests.get(url, headers=headers).text, features='lxml')
        cur.append('Date: ' + soup.find('meta', {'property': "article:published_time"})['content'])
        cur.append('Author: ' + soup.find('div', {'class': "post__author_name-text"}).text)
        cur.append(soup('title')[0].text)
        article = ''
        for p in soup.findAll('p'):
            article += p.text + '\n'
        article = article[article.find('\n') + 1:]
        cur.append('Body: ' + article)
        articles.append(article)
        with open('mozhga_corpus.txt', 'a', encoding='utf-8') as f:
            f.write('\n'.join(cur))
            f.write('\n=====\n')
    return articles


def display_fragments(indices, articles, window=0):
    if not indices:
        print('Такого слова нет')
    else:
        for occurence in indices:
            i, j = occurence[0], occurence[1]
            print(i, j)
            print(' '.join(articles[i][((j-window)*(j-window >= 0)):((j+window+2)*(j+window+2 <= len(articles[i]) + 1) - 1)]))


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'}
new_urls = iterate_main_page(headers)
articles = extract_news(new_urls, headers)
for i, text in enumerate(articles):
    articles[i] = parse_text(text)
tree = {}
for i, text in enumerate(articles):
    for j, word in enumerate(text):
        add_word_to_tree(tree, word, (i, j))
print(tree)
word = input('Input word: ')
indices = find_word(tree, word)
display_fragments(indices, articles, window=3)
