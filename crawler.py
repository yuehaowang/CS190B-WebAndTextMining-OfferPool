from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import re
import sys
import json


'''
Configs
'''

FORUM_URLS = [
	'http://bbs.gter.net/forum-49-%s.html'
]

PAGE_TIMEOUT = 15


'''
Crawler class
'''

class Crawler:
	def __init__(self):
		opt = Options()
		# opt.add_argument('--headless')
		self.browser = self._create_browser()

		self.max_page = 1

	def start(self, forum_url):
		cur_page = 1

		while cur_page <= self.max_page:
			# open forum page
			page_url = forum_url % cur_page
			# list of posts
			posts = []

			self.browser.get(page_url)

			# fetch all post items
			res = self.browser.find_elements_by_css_selector('tbody[id^="normalthread_"] .new')
			for item in res:
				try:
					tag_elem = item.find_element_by_css_selector('em')
					tag_txt = tag_elem.text
				except:
					tag_txt = ''

				title_elem = item.find_element_by_css_selector('a.xst')

				posts.append({
					'tag_txt': tag_txt,
					'title_txt': title_elem.text,
					'title_url': title_elem.get_attribute('href')
				})

			# crawl each post
			for o in posts:
				if re.match(r'^\[Offer.+\]', o['tag_txt']):  # an offer post
					self._crawl_offer(o['title_url'])

			cur_page += 1

	def _create_browser(self):
		opt = Options()
		# disable js
		opt.add_experimental_option( "prefs",{'profile.managed_default_content_settings.javascript': 2})
		# headless mode
		# opt.add_argument('--headless')
		browser = webdriver.Chrome(
			executable_path='./chromedriver',
			chrome_options=opt
		)

		return browser

	def _crawl_offer(self, url):
		self.browser.get(url)

		try:
			profile = {
				'offers': [],
				'person': {}
			}

			# read offer information
			offer_res = self.browser.find_elements_by_css_selector('table[summary^="offer"]')
			for t in offer_res:
				offer = {}
				lines = t.text.split('\n')

				for ln in lines:
					ln_tokens = ln.split(': ')

					if len(ln_tokens) < 2:
						continue

					field_name = ln_tokens[0]
					value = ': '.join(ln_tokens[1:])
					if field_name == '申请学校':
						field_name = 'school'
					elif field_name == '学位':
						field_name = 'degree'
					elif field_name == '专业':
						field_name = 'major'
					elif field_name == '申请结果':
						field_name = 'result'
					elif field_name == '入学年份':
						field_name = 'enroll_time'
					elif field_name == '入学学期':
						field_name = 'enroll_term'
					else:
						continue

					offer[field_name] = value
					profile['offers'].append(offer)

			# read person information
			person_res = self.browser.find_elements_by_css_selector('table[summary^="个人情况"]')
			for t in person_res:
				lines = t.text.split('\n')
				other_info = ''

				for ln in lines:
					ln_tokens = ln.split(': ')

					if len(ln_tokens) < 2:
						continue

					field_name = ln_tokens[0]
					value = ': '.join(ln_tokens[1:])
					if field_name == 'TOEFL':
						field_name = 'toefl'
					elif field_name == 'GRE':
						field_name = 'gre'
					elif field_name == '本科学校档次':
						field_name = 'undergra_school'
					elif field_name == '本科专业':
						field_name = 'undergra_major'
					elif field_name == '本科成绩和算法、排名':
						field_name = 'undergra_grade'
					elif field_name == '研究生专业':
						field_name = 'graduate_major'
					elif field_name == '研究生学校档次':
						field_name = 'graduate_school'
					elif field_name == '研究生成绩和算法、排名':
						field_name = 'graduate_grade'
					else:
						other_info += value + '\n'

						continue

					profile['person'][field_name] = value

				profile['person']['others'] = other_info

			r = json.dumps(profile, ensure_ascii=False)
			print(r)

		except NoSuchElementException:
			pass
		except Exception as err:
			raise err

	def close(self):
		self.browser.close()


if __name__ == "__main__":
	crawler = Crawler()
	for url in FORUM_URLS:
		crawler.start(url)

	crawler.close()