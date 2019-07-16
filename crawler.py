from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import os
import json
import time


'''
Configs
'''

FORUM_URLS = [
	'http://bbs.gter.net/forum-49-%s.html'
]

PAGE_LOAD_TIMEOUT = int(os.getenv('OFFERPOOL_CRAWLER_PAGE_LOAD_TIMEOUT', 5))

'''
Terminal text style
'''

class termstyl:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'

	@staticmethod
	def bold(txt):
		return termstyl.BOLD + txt + termstyl.ENDC

	@staticmethod
	def header(txt):
		return termstyl.HEADER + txt + termstyl.ENDC

	@staticmethod
	def okgreen(txt):
		return termstyl.OKGREEN + txt + termstyl.ENDC

	@staticmethod
	def okblue(txt):
		return termstyl.OKBLUE + txt + termstyl.ENDC

	@staticmethod
	def fail(txt):
		return termstyl.FAIL + txt + termstyl.ENDC

	@staticmethod
	def warning(txt):
		return termstyl.WARNING + txt + termstyl.ENDC

'''
Crawler class
'''

class Crawler:
	def __init__(self):
		self.browser = self._create_browser()

		self.start_page = int(os.getenv('OFFERPOOL_CRAWLER_START_PAGE', 1))
		self.end_page = int(os.getenv('OFFERPOOL_CRAWLER_END_PAGE', 100))

	def start(self, forum_url):
		cur_page = self.start_page
		num_crawled_posts = 0

		start_time = time.time()

		print(termstyl.header('Crawler started!\n'))

		while cur_page <= self.end_page:
			# url of forum page
			page_url = forum_url % cur_page
			# list of posts 
			posts = []

			try:
				self.browser.get(page_url)
				WebDriverWait(self.browser, PAGE_LOAD_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'threadlist')))
			except TimeoutException:
				print(termstyl.warning('Cannot open page %d. Retrying...' % cur_page))
				continue

			# fetch all post items
			res = self.browser.find_elements_by_css_selector('tbody[id^="normalthread_"] .%s' % 'common')

			if not res:
				res = self.browser.find_elements_by_css_selector('tbody[id^="normalthread_"] .%s' % 'new')

			for item in res:
				try:
					tag_elem = item.find_element_by_css_selector('em')
					tag_txt = tag_elem.text
				except:
					tag_txt = ''
					print(termstyl.warning('No post tag: %s' % item.text))

				try:
					title_elem = item.find_element_by_css_selector('a.xst')
				except Exception as err:
					print(termstyl.fail('Post link not found: %s' % item.text))

				posts.append({
					'tag_txt': tag_txt,
					'title_txt': title_elem.text,
					'title_url': title_elem.get_attribute('href')
				})

			# crawl each post
			for o in posts:
				if re.match(r'^\[Offer.+\]', o['tag_txt']):  # an offer post
					print('%s: %s' % (termstyl.bold('Crawling'), o['title_url']))

					if self._crawl_offer(o['title_url']):
						num_crawled_posts += 1

					if num_crawled_posts % 50 == 0:
						print(termstyl.okblue('Crawled %s posts' % num_crawled_posts))

			cur_page += 1

		# complete message
		print(
			termstyl.bold(termstyl.okgreen('Done.')),
			termstyl.okblue('%.3f' % (time.time() - start_time)) + termstyl.okgreen(' seconds used.'),
			termstyl.header('Total posts: %d, total pages: %d.' % (num_crawled_posts, cur_page - self.start_page))
		)

	def _create_browser(self):
		opt = Options()
		print(termstyl.okblue('Creating web driver...'))

		# page load strategy: none
		caps = DesiredCapabilities().CHROME
		caps['pageLoadStrategy'] = 'none'
		print(termstyl.okblue('Web driver pageLoadStrategy: none'))

		# headless mode
		opt.headless = True
		opt.add_argument('--disable-gpu')
		print(termstyl.okblue('Web driver: run in headless mode'))

		browser = webdriver.Chrome(
			executable_path='C:/Users/Nizhenghao/Desktop/WebAndTextMining/OfferPool/chromedriver.exe',
			desired_capabilities=caps,
			options=opt
		)
		print(termstyl.okblue('Web driver created.'))

		return browser

	@staticmethod
	def _get_post_name(url):
		tokens = url.split('/')

		if len(tokens) > 1:
			slug = tokens[-1]
			return '.'.join(slug.split('.')[0:-1])

	def _crawl_offer(self, url):
		try:
			self.browser.get(url)
			WebDriverWait(self.browser, PAGE_LOAD_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'f_pst')))
			WebDriverWait(self.browser, PAGE_LOAD_TIMEOUT).until(EC.presence_of_element_located((By.CLASS_NAME, 'f-main-footer')))
		except:
			print(termstyl.warning('Cannot open post %s' % url))
			return False

		try:
			profile = {
				'url': url,
				'offers': [],
				'person': {}
			}

			# read offer information
			offer_res = self.browser.find_elements_by_css_selector('table[summary^="offer"]')

			if len(offer_res) < 1:
				print(termstyl.warning('Offer info missing: %s, page ignored' % url))
				return False

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
					elif field_name == 'IELTS':
						field_name = 'ielts'
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

			try:
				# extract post name from slug
				post_name = self._get_post_name(url)
				if post_name:
					# save data
					with open('C:/Users/Nizhenghao/Desktop/WebAndTextMining/OfferPool/data/%s.json' % post_name, 'w+') as f:
						r = json.dumps(profile, ensure_ascii=False, indent=4)
						f.write(r)
			except:
				print(termstyl.fail('Cannot save post: %s' % url))

		except (NoSuchElementException, TimeoutException):
			print(termstyl.warning('Post info missing: %s' % url))

		return True

	def close(self):
		self.browser.close()


if __name__ == '__main__':
	crawler = Crawler()
	for url in FORUM_URLS:
		crawler.start(url)

	crawler.close()
