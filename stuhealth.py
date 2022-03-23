from datetime import datetime, timedelta
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import algorithms
from Crypto.Cipher import AES
from random import choice
from base64 import b64encode
import requests
from json import loads
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.utils import formataddr

def pkcs7_padding(data):
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data.encode('utf-8')) + padder.finalize()
    return padded_data
def encrypt(data):
    key = 'xAt9Ye&SouxCJziN'.encode('utf-8')
    cryptor = AES.new(key,AES.MODE_CBC,key)
    return b64encode(cryptor.encrypt(pkcs7_padding(data))).decode().replace('/','_').replace('+','-')
def req(u,d):
    res = requests.post(u,json = d,headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
        'Referer': 'https://stuhealth.jnu.edu.cn/'
    })
    res.encoding = 'utf8'
    if res.status_code == requests.codes.ok:
        return loads(res.text)
    raise RuntimeError('Req-Error: ' + str(res.status_code) + '\nText: ' + res.text)
def clean(tb,l):
    if not tb:
        raise RuntimeError('Table-TypeError')
    for key in list(tb):
        if not tb[key] or key in l:
            tb.pop(key)
    return tb
def mail(rec,msg):
    message = MIMEText(msg,'plain','utf-8')
    message['Subject'] = 'Stuhealth'
    message['From'] = formataddr(['Script','lakwsh@lakwsh.net'])
    try:
        smtp = SMTP_SSL('smtp.exmail.qq.com')
        smtp.connect('smtp.exmail.qq.com',465)
        smtp.login('lakwsh@lakwsh.net','邮箱密码')
        smtp.sendmail('lakwsh@lakwsh.net',rec,message.as_string())
        smtp.quit()
    except Exception as e:
        print(msg)
        print(str(e))
        exit(1)
def getvalidate():
    res = requests.get('过滑块验证码api')
    if res.status_code == requests.codes.ok:
        return res.text
    raise RuntimeError('Get-Failed: ' + str(res.status_code))

ul = {'2019000000':'密码'}
result = str(datetime.now())
try:
    for usr,pwd in ul.items():
        try:
            validate = getvalidate()
        except:
            validate = getvalidate()
        ret = req('https://stuhealth.jnu.edu.cn/api/user/login',{'username':usr,'password':encrypt(pwd).replace('=','*',1),'validate':validate})
        meta = ret['meta']
        result += '\n' + usr + ' => ' + meta['msg']
        if meta['code'] == 200:
            jid = ret['data']['jnuid']
            ret = req('https://stuhealth.jnu.edu.cn/api/user/stuinfo',{'jnuid':jid,'idType':ret['data']['idtype']})
            data = ret['data']
            mt = clean(data['mainTable'],['id','personType','createTime','del'])
            mt['personName'] = data['xm']
            mt['sex'] = data['xbm']
            mt['professionName'] = data['zy']
            mt['collegeName'] = data['yxsmc']
            mt['declareTime'] = data['declare_time']
            st = clean(data['secondTable'],['id','mainId'])
            st['other29'] = '35.' + choice('45678')
            st['other31'] = '36.' + choice('12345')
            st['other33'] = '35.' + choice('56789')
            st['other30'] = st['other32'] = st['other34'] = str(datetime.today()+timedelta(days = -1))
            ret = req('https://stuhealth.jnu.edu.cn/api/write/main',{'mainTable':mt,'secondTable':st,'jnuid':jid})
            result += '\n' + ret['meta']['msg']
            result += '\nTime => ' + ret['meta']['timestamp']
    mail(['someone@lakwsh.net'],result)
except Exception as e:
    mail(['error@lakwsh.net'],result + '\nLine-' + str(e.__traceback__.tb_lineno) + ': ' + str(e))
