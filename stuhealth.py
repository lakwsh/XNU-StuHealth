from time import sleep
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
	h = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
		'Referer': 'https://stuhealth.jnu.edu.cn/'
	}
	for _ in range(3):
		res = requests.post(u,json = d,headers = h)
		res.encoding = 'utf8'
		if res.status_code == requests.codes.ok:
			return loads(res.text)
		sleep(1)
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
	message['From'] = formataddr(['Script','发件邮箱'])
	try:
		smtp = SMTP_SSL('邮箱服务器')
		smtp.connect('邮箱服务器',465)
		smtp.login('邮箱用户名','邮箱密码')
		smtp.sendmail('发件邮箱',rec,message.as_string())
		smtp.quit()
	except Exception as e:
		print(msg)
		print(str(e))
		exit(1)
def getvalidate():
	for _ in range(2):
		res = requests.get('滑块api地址')
		if res.status_code == requests.codes.ok:
			return res.text
	raise RuntimeError('Get-Failed: ' + str(res.status_code))

ul = {'学号1':'密码1','学号2':'密码2'}
result = str(datetime.now())
try:
	for usr,pwd in ul.items():
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
			sleep(1)
			ret = req('https://stuhealth.jnu.edu.cn/api/write/main',{'mainTable':mt,'secondTable':st,'jnuid':jid})
			result += '\n' + ret['meta']['msg']
			result += '\nTime => ' + ret['meta']['timestamp']
		sleep(2)
	mail(['打卡成功邮箱'],result)
except Exception as e:
	mail(['打卡错误邮箱'],result + '\nLine-' + str(e.__traceback__.tb_lineno) + ': ' + str(e))
