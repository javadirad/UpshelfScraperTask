from tkinter import EXCEPTION
import scrapy
import json

class MainSpider(scrapy.Spider):
    name = 'mainspider'
    start_urls = ['https://www.target.com/p/apple-iphone-13-pro-max/-/A-84616123?preselect=84240109#lnk=sametab']
    questions_url = 'https://r2d2.target.com/ggc/Q&A/v1/question-answer?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&page={}&questionedId=84616123&type=product&size=10&sortBy=MOST_ANSWERS&errorTag=drax_domain_questions_api_error'

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.QuestionCounter = 1
        self.Result = {}

    def parse(self, response):
        data = response.css('script::text').getall()[2].replace('\\','')
        txt = 'window.__TGT_DATA__ = JSON.parse("'
        fromindex = data.find(txt)+len(txt)
        txt = '");\nwindow.__WEB_CLUSTER__ = \'prod\';'
        toindex = data.find(txt)
        data = data[fromindex:toindex]
        jsData = json.loads(data)
        description = response.css('div.h-margin-v-default::text').getall()
        specifications = {}
        for  specification in  response.css('div[data-test="item-details-specifications"]').css('div'):
            if specification.css('b::text').get() == None:
                continue
            specifications[specification.css('b::text').get().replace(':','')] = ''.join(specification.css('div::text').getall()).replace(':','')
        highlights = [highlight.css('span::text').get() for highlight in response.css('li.styles__Bullet-sc-6aebpn-0')]
 
 
        images = response.css('div.styles__CarouselProductThumbnailWrapper-sc-cwwbs3-1')
         
        self.Result['title'] =response.xpath('/html/body/div[1]/div[2]/div/div[2]/div[1]/div[1]/h1/span/text()').get()
        self.Result['price'] = jsData['__PRELOADED_QUERIES__']['queries'][1][1]['product']['children'][0]['price']['current_retail']
        self.Result['description'] = ' \n '.join(description)
        self.Result['specifications'] =  specifications
        self.Result['highlights'] =  ' \n '.join(highlights)
        self.Result['questions'] =  []
        self.Result['images urls'] =  [img.attrib['src'] for img in images.css('img') if img.attrib['src'].startswith('https:/')],

         

        yield scrapy.Request(self.questions_url.format(0), callback=self.parse_questions)
    def parse_questions(self, response):
        jsonresponse = json.loads(response.body)
        ls = []
        for question in jsonresponse['results']:
            ls.append(
                {
                    f'Q{self.QuestionCounter}':question['text'],
                    f'answers':{f'ANS{i}':answers['text'] for i,answers in enumerate(question['answers'])}
                }
            )
            self.QuestionCounter += 1
        self.Result['questions'].append(ls)
        
        if not jsonresponse['last_page']:            
            yield scrapy.Request(self.questions_url.format(int(jsonresponse['page'])+1), callback=self.parse_questions)
        else:
            yield self.Result
        
if __name__ == '__main__':
    import os
    from scrapy.cmdline import execute

    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    SPIDER_NAME = MainSpider.name
    try:
        execute(
            [
                'scrapy',
                'crawl',
                SPIDER_NAME,
                '-O',
                'output.json',
            ]
        )
    except SystemExit as e:
        pass