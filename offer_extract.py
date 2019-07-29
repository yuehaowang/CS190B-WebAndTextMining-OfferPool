import json
import os
import re
import csv

DATA_PATH = './data/'

def ielts_to_toefl(score):
	if score <= 4:
		return 31 * (score / 4)
	elif score <= 4.5:
		return 34 * (score / 4.5)
	elif score <= 5:
		return 45 * (score / 5)
	elif score <= 5.5:
		return 59 * (score / 5.5)
	elif score <= 6:
		return 78 * (score / 6)
	elif score <= 6.5:
		return 93 * (score / 6.5)
	elif score <= 7:
		return 101 * (score / 7)
	elif score <= 7.5:
		return 109 * (score / 7.5)
	elif score <= 8:
		return 114 * (score / 8)
	elif score <= 8.5:
		return 117 * (score / 8.5)
	elif score <= 9:
		return 120 * (score / 9)

def get_english_overall_score(txt, max_score):
	try:
		n = float(txt)
	except ValueError:
		start = txt.find('Overall: ')
		end = txt.find(',')

		if start < 0 or end < 0:
			return None

		score_txt = txt[start + 9:end]

		try:
			n = float(score_txt)
		except ValueError:
			return None

	if n > max_score:
		return None

	return n

def keep_letters_numbers_spaces(s):
	return re.sub(r'[^a-zA-Z0-9_\s]', '', s)

def load_dict(file):
	with open(file, 'r') as f:
		return json.loads(f.read())

	return {}

if __name__ == "__main__":
	univ_dict = {}

	major_dict = load_dict('major_dict.json')

	person_id = 0

	with open('all.csv', 'w+') as output_file:
		fieldnames = ['pid', 'toefl', 'gre', 'undergra_major', 'undergra_grade', 'school', 'degree', 'major', 'apply_result']
		writer = csv.DictWriter(output_file, fieldnames, delimiter='\t')
		writer.writeheader()

		for (_, _, filenames) in os.walk(DATA_PATH):
			for filename in filenames:
				if not re.match(r'^thread-\d+-\d+-\d+.json$', filename):
					continue

				with open(DATA_PATH + filename) as f:
					profile = json.loads(f.read())

					if not 'person' in profile or not 'offers' in profile:
						continue

					person = profile['person']
					offers = profile['offers']

					#################################################
					## English
					################################################
					if 'toefl' in person:
						res = get_english_overall_score(person['toefl'], 120)

						if res:
							toefl_score = res
						else:
							continue
					else:
						continue

					if 'ielts' in person:
						res = get_english_overall_score(person['ielts'], 9)

						if res:
							if res > toefl_score:
								toefl_score = ielts_to_toefl(res)
						else:
							continue

					if 'gre' in person:
						res = get_english_overall_score(person['gre'], 346)

						if res:
							gre_score = res
						else:
							continue
					else:
						continue

					#################################################
					## GPA
					################################################
					if 'undergra_grade' in person:
						res = person['undergra_grade']

						ls = re.findall("\d+\.\d+|\d+", res)

						if len(ls) > 0:
							n = float(ls[0])

							if n > 4:
								n = (n / 100) * 4

							if n < 1:
								continue

							gpa = n
						else:
							continue
					else:
						continue

					#################################################
					## Major
					################################################
					if 'undergra_major' in person:
						res = person['undergra_major']

						if res in major_dict:
							undergra_major = major_dict[res]
						else:
							continue
					else:
						continue

					#################################################
					## person id
					################################################
					person_id += 1


					for offer in offers:

						#################################################
						## School
						################################################
						if 'school' in offer:
							school = keep_letters_numbers_spaces(offer['school'])

							if school in univ_dict:
								univ_dict[school] += 1
							else:
								univ_dict[school] = 1
						else:
							continue

						#################################################
						## AD or offer
						################################################
						if 'result' in offer:
							res = offer['result'].lower()

							if res.find('offer') >= 0:
								apply_result = 'offer'
							elif res.find('ad') >= 0:
								apply_result = 'ad'
							elif res.find('被拒') >= 0:
								apply_result = 'reject'
							else:
								continue
						else:
							continue

						#################################################
						## degree
						################################################
						if 'degree' in offer:
							res = keep_letters_numbers_spaces(offer['degree'].lower())

							if len(res.strip()) > 0:
								degree = res
							else:
								continue
						else:
							continue

						#################################################
						## degree
						################################################
						if 'major' in offer:
							res = keep_letters_numbers_spaces(offer['major'])

							if len(res.strip()) > 0:
								major = res
							else:
								continue


						writer.writerow({
							'pid': person_id,
							'toefl': toefl_score,
							'gre': gre_score,
							'undergra_major': undergra_major.strip(),
							'undergra_grade': gpa,
							'school': school.strip(),
							'degree': degree.strip(),
							'major': major.strip(),
							'apply_result': apply_result.strip()
						})
