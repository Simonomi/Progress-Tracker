showBrowser = True
browserTimeout = 300

def getSourceCode(url):
	from requests import get
	return get(url).text


# Takes in a date as "m-d-y"
def dateHasPassed(date):
	from datetime import datetime
	
	month = int(date.split("-")[0])
	day = int(date.split("-")[1])
	year = int(date.split("-")[2])
	timeSince = datetime.now() - datetime(month, day, year)
	return timeSince.days >= 0


def parseLink(link, season, episode, totalEpisode):
	while "[e" in link:
		code = link.split("[e")[1].split("]")[0]
		if len(code) == 0:
			link = link.replace("[e]", str(episode))
		else:
			signifier = "[e{}]".format(code)
			if code[0] == "0":
				if "+" in code:
					episode = episode + int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index(
						"+")]) + 1 - len(str(episode))) + str(episode))
				elif "-" in code:
					episode = episode - int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index(
						"-")]) + 1 - len(str(episode))) + str(episode))
				else:
					link = link.replace(signifier, "0" * (len(code) + 1 - len(str(
						episode))) + str(episode))
			elif code[0] == "+":
				link = link.replace(signifier, str(episode + int(code[1:])))
			elif code[0] == "-":
				link = link.replace(signifier, str(episode + int(code[1:])))
			elif code[:2] == "nd":
				mod = str(episode)
				if episode > 10 and episode < 20:
					mod += "th"
				else:
					if episode % 10 == 1:
						mod += "st"
					elif episode % 10 == 2:
						mod += "nd"
					elif episode % 10 == 3:
						mod += "rd"
					else:
						mod += "th"
				link = link.replace("[end]", mod)
	while "[te" in link:
		code = link.split("[te")[1].split("]")[0]
		if len(code) == 0:
			link = link.replace("[te]", str(totalEpisode))
		else:
			signifier = "[te{}]".format(code)
			if code[0] == "0":
				if "+" in code:
					totalEpisode = totalEpisode + int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index(
						"+")]) + 1 - len(str(totalEpisode))) + str(totalEpisode))
				elif "-" in code:
					totalEpisode = totalEpisode - int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index(
						"-")]) + 1 - len(str(totalEpisode))) + str(totalEpisode))
				else:
					link = link.replace(signifier, "0" * (len(code) + 1 - len(str(
						totalEpisode))) + str(totalEpisode))
			elif code[0] == "+":
				link = link.replace(signifier, str(totalEpisode + int(code[1:])))
			elif code[0] == "-":
				link = link.replace(signifier, str(totalEpisode + int(code[1:])))
			elif code[:2] == "nd":
				mod = str(totalEpisode)
				if totalEpisode > 10 and totalEpisode < 20:
					mod += "th"
				else:
					if totalEpisode % 10 == 1:
						mod += "st"
					elif totalEpisode % 10 == 2:
						mod += "nd"
					elif totalEpisode % 10 == 3:
						mod += "rd"
					else:
						mod += "th"
				link = link.replace("[tend]", mod)
	while "[s" in link:
		code = link.split("[s")[1].split("]")[0]
		if len(code) == 0:
			link = link.replace("[s]", str(season))
		else:
			signifier = "[s{}]".format(code)
			if code[0] == "0":
				if "+" in code:
					season = season + int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index(
						"+")]) + 1 - len(str(season))) + str(season))
				elif "-" in code:
					season = season - int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index(
						"-")]) + 1 - len(str(season))) + str(season))
				else:
					link = link.replace(signifier, "0" * (len(code) + 1 - len(str(
						season))) + str(season))
			elif code[0] == "+":
				link = link.replace(signifier, str(season + int(code[1:])))
			elif code[0] == "-":
				link = link.replace(signifier, str(season + int(code[1:])))
			elif code[:2] == "nd":
				mod = str(season)
				if season > 10 and season < 20:
					mod += "th"
				else:
					if season % 10 == 1:
						mod += "st"
					elif season % 10 == 2:
						mod += "nd"
					elif season % 10 == 3:
						mod += "rd"
					else:
						mod += "th"
				link = link.replace("[snd]", mod)
	while "[b64]" in link:
		from base64 import b64encode
		code = link.split("[b64]")[1].split("[/b64]")[0]
		link = link.replace("[b64]{}[/b64]".format(code),
			b64encode(bytes(code, "UTF-8")).decode("utf-8").strip("="))
	
	return link


def runCommands(instructions, string):
	string = [string]
	
	for i in range(len(instructions)):
		word = instructions[i]
		
		if word in ["getElementAttribute", "getElementAttributeClicks", "replace",
				"split", "insert", "remove", "combine", "debase", "add"]:
			index = int(instructions[i + 1])
			
			if word == "getElementAttribute":
				results = getElementAttribute(instructions[i + 2].format(
					string[index]), instructions[i + 3], instructions[i + 4])
				if results == [] or results == None:
					return ""
				
				string[index] = results[int(instructions[i + 5])]
			elif word == "getElementAttributeClicks":
				results = getElementAttribute(instructions[i + 3].format(
					string[index]), instructions[i + 4], instructions[i + 5],
					instructions[i + 6:i + int(instructions[i + 2]) + 6])
				if results == []:
					return ""
				
				string[index] = results[int(instructions[i + int(instructions[
					i + 2]) + 7])]
			elif word == "replace":
				string[index] = string[index].replace(instructions[i + 2],
					instructions[i + 3])
			elif word == "split":
				from re import split
				string = string[:index] + split(instructions[i + 2], string[
					index]) + string[index + 1:]
			elif word == "insert":
				string.insert(index, instructions[i + 2])
			elif word == "remove":
				string.pop(index)
			elif word == "combine":
				string[index] = str(string[index]) + str(string[int(instructions[
					i + 2])])
				string.pop(int(instructions[i + 2]))
			elif word == "debase":
				from base64 import b64decode
				string[index] = b64decode(bytes(string[index] + (len(string[
					index]) % 4 * "="), "UTF-8")).decode("utf-8")
			elif word == "add":
				string[index] = str(int(string[index]) + int(instructions[i + 2]))

	return "".join(string)


def getElementAttribute(url, element, attribute, clicks=[]):
	# try:
	from lxml import etree
	from requests import get, exceptions
	import urllib.request
	
	try:
		html = get(url).text
	except:
		html = ""
	
	try:
		if len(clicks) > 0:
			raise IndexError
		
		root = etree.HTML(html)
		
		output = []
		for i in root.cssselect(element):
			output.append(i.get(attribute))
			if output[-1][0] == "/":
				output[-1] = "/".join(url.split("/")[:3]) + output[-1]
		
		if not output:
			raise IndexError
		
		return output
	except (IndexError, AttributeError):
		from selenium import webdriver
		from selenium.webdriver.support import expected_conditions as EC
		from selenium.webdriver.support.ui import WebDriverWait
		from selenium.webdriver.common.by import By
		from selenium.common.exceptions import TimeoutException
		
		options = webdriver.ChromeOptions()
		if not showBrowser:
			options.add_argument("--window-size=0,0")
			options.add_argument("--window-position=3000,3000")
		
		options.add_argument("--disable-blink-features=AutomationControlled")
		options.add_experimental_option("excludeSwitches", ["enable-automation"])
		options.add_experimental_option('excludeSwitches', ['enable-logging'])
		options.add_experimental_option('useAutomationExtension', False)
		
		browser = webdriver.Chrome("C:\Program Files\ChromeDriver\chromedriver.exe", options=options)
		if not showBrowser:
			browser.minimize_window()
		
		browser.get(url)
		
		# browser.execute_script("window.open('/');")
		if not showBrowser:
			browser.minimize_window()
		
		try:
			for i in clicks:
				while True:
					try:
						print("click")
						print(i)
						WebDriverWait(browser, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, i))).click()
						break
					except:
						pass
			WebDriverWait(browser, browserTimeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "{0}[{1}]".format(element, attribute))))
		except TimeoutException:
			browser.quit()
			return []
		
		html = browser.page_source.encode("cp1252", "ignore").decode('cp1252')
		
		browser.quit()
		
		root = etree.HTML(html)
		
		output = []
		for i in root.cssselect(element):
			output.append(i.get(attribute))
			if output[-1][0] == "/":
				output[-1] = "/".join(url.split("/")[:3]) + output[-1]
		
		return output
	# except:
		# print("fail")
		# pass
