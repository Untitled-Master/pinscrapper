import re
import json
from requests import get
from bs4 import BeautifulSoup as soup
from pydotmap import DotMap
from concurrent.futures import ThreadPoolExecutor


class PinterestImageScraper:

    def __init__(self):
        self.json_data_list = []

    @staticmethod
    def get_pinterest_links(body, max_images):
        searched_urls = []
        html = soup(body, 'html.parser')
        links = html.select('#main > div > div > div > a')
        for link in links:
            link = link.get('href')
            link = re.sub(r'/url\?q=', '', link)
            if link[0] != "/" and "pinterest" in link:
                searched_urls.append(link)
                if max_images is not None and max_images == len(searched_urls):
                    break

        return searched_urls

    def get_source(self, url, proxies):
        try:
            res = get(url, proxies=proxies)
        except Exception as e:
            return
        html = soup(res.text, 'html.parser')
        json_data = html.find_all("script", attrs={"id": "__PWS_DATA__"})
        for a in json_data:
            self.json_data_list.append(a.string)

    def save_image_url(self, max_images):
        url_list = [i for i in self.json_data_list if i.strip()]
        if not len(url_list):
            return url_list
        url_list = []
        for js in self.json_data_list:
            try:
                data = DotMap(json.loads(js))
                urls = []
                for pin in data.props.initialReduxState.pins:
                    if isinstance(data.props.initialReduxState.pins[pin].images.get("orig"), list):
                        for i in data.props.initialReduxState.pins[pin].images.get("orig"):
                            urls.append(i.get("url"))
                    else:
                        urls.append(data.props.initialReduxState.pins[pin].images.get("orig").get("url"))

                for url in urls:
                    url_list.append(url)
                    if max_images is not None and max_images == len(url_list):
                        return list(set(url_list))

            except Exception as e:
                continue

        return list(set(url_list))

    def scrape(self, key=None, proxies={}, max_images=None, threads=5):
        extracted_urls = self.get_pinterest_links(get(f'http://www.google.co.in/search?hl=en&q={key} pinterest', proxies=proxies).content, max_images)
        return_data = {}
        self.json_data_list = []

        with ThreadPoolExecutor(max_workers=threads) as executor:
            for i in extracted_urls:
                executor.submit(self.get_source, i, proxies)

        url_list = self.save_image_url(max_images)

        return_data = {
            "url_list": url_list[:max_images] if max_images is not None else url_list,
            "extracted_urls": extracted_urls,
            "keyword": key
        }

        return return_data


scraper = PinterestImageScraper()

if __name__ == "__main__":
    num_images = 1
    details = scraper.scrape("chess", max_images=num_images, threads=10)

    print("Image Links:")
    for url in details["url_list"]:
        print(url)
