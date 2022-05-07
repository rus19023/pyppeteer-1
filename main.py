import asyncio
from pyppeteer import launch
import requests
import csv



jsForTextReview = """
(element) =>{
	reviewEl = element.childNodes[0].childNodes[1].childNodes[1].childNodes;
	returnData = {"dign":"-","fail":"-","comment":"-","review":"-","photos":[]};
	for (var i = 0;i<reviewEl.length;i++){
	    if (reviewEl[i].querySelectorAll('div')[0].textContent.includes('Достоинства')){
	        returnData['dign'] = reviewEl[i].querySelectorAll('div')[1].textContent
	    }
	    else if (reviewEl[i].querySelectorAll('div')[0].textContent.includes('Недостатки')){
	        returnData['fail'] = reviewEl[i].querySelectorAll('div')[1].textContent
	    }
	    else if (reviewEl[i].querySelectorAll('div')[0].textContent.includes('Комментарий')){
	        returnData['comment'] = reviewEl[i].querySelectorAll('div')[1].textContent
	    }
	    else{
	        returnData['review'] = reviewEl[i].querySelectorAll('div')[0].textContent
	    }
	}
	try{
		photosEl = element.childNodes[0].childNodes[1].childNodes[2].querySelectorAll('img');
		for (var i = 0; i< photosEl.length; i++){
			returnData['photos'].push(photosEl[i].src)
		}
	}catch{

	}

	return returnData;
}
"""


async def downloadPhoto(url):
	name = url.split('/')[-1]
	with open('images/'+name, 'wb') as file:
		r = requests.get(url)
		file.write(r.content)


async def get_links():
	with open('links.txt','r',encoding='utf-8') as file:
		data = file.readlines()
	return data


async def work(page):
	data = []
	links = await get_links()
	for l in links:
		pagination = 1
		while True:
			await page.goto(l+'reviews/?page=%s' % pagination)
			await page.waitForSelector('div[data-widget=listReviewsDesktop]>div')
			pagination += 1
			elClass = await page.evaluate('(elements) => elements.childNodes[0].className', (await page.querySelectorAll('div[data-widget=listReviewsDesktop]>div'))[1])
			try:
				elements = await page.querySelectorAll('.'+elClass)
			except:
				break
			if len(elements)==0:
				break
			for el in elements:
				name = await page.evaluate('(element) => element.textContent',(await el.querySelectorAll('span'))[1])
				date = await page.evaluate('(date) => date.childNodes[0].childNodes[0].childNodes[1].childNodes[0].textContent', el)
				rate = await page.evaluate('(rate) => rate.style.width',await el.querySelector('.ui-ba8'))
				rate = int(int(rate.replace('%',''))/20)
				eltext = await page.evaluate(jsForTextReview,el)
				dign = eltext['dign']
				fail = eltext['fail']
				comment = eltext['comment']
				review = eltext['review']
				allPhotos = eltext['photos']
				photos = ''
				for p in allPhotos:
					await downloadPhoto(p)
					photos+=(p.split('/')[-1]+'; ')
				data.append([l.strip(), name.strip(), date.strip(), rate, dign.strip(), fail.strip(), comment.strip(), review.strip(), photos.strip()])
	with open('result.csv', 'w', encoding='utf-8') as file:
		writer = csv.writer(file, delimiter='#', quotechar=' ')
		writer.writerow(["Товар","Имя","Дата","Оценка","Достоинства","Недостатки","Комментарий","Отзыв","Фотографии"])
		writer.writerows(data)


async def main():
	params = {'headless': True}
	browser = await launch(**params)
	page = await browser.newPage()
	await work(page)
	await browser.close()


if __name__ == '__main__':
	asyncio.get_event_loop().run_until_complete(main())