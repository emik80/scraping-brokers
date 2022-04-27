import re
import requests
from bs4 import BeautifulSoup
import csv
import os

url = 'https://brokers.interexo.com/search?country%5B0%5D=United%20States&state%5B0%5D=Alabama&state%5B1%5D=Alaska&state%5B2%5D=Arizona&state%5B3%5D=Arkansas&state%5B4%5D=California&state%5B5%5D=Colorado&state%5B6%5D=Connecticut&state%5B7%5D=Delaware&state%5B8%5D=District%20of%20Columbia&state%5B9%5D=Florida&state%5B10%5D=Georgia&state%5B11%5D=Hawaii&state%5B12%5D=Idaho&state%5B13%5D=Illinois&state%5B14%5D=Indiana&state%5B15%5D=Iowa&state%5B16%5D=Kansas&state%5B17%5D=Kentucky&state%5B18%5D=Louisiana&state%5B19%5D=Maine&state%5B20%5D=Maryland&state%5B21%5D=Massachusetts&state%5B22%5D=Michigan&state%5B23%5D=Minnesota&state%5B24%5D=Mississippi&state%5B25%5D=Missouri&state%5B26%5D=Montana&state%5B27%5D=Nebraska&state%5B28%5D=Nevada&state%5B29%5D=New%20Hampshire&state%5B30%5D=New%20Jersey&state%5B31%5D=New%20Mexico&state%5B32%5D=New%20York&state%5B33%5D=North%20Carolina&state%5B34%5D=Ohio&state%5B35%5D=Oklahoma&state%5B36%5D=Oregon&state%5B37%5D=Pennsylvania&state%5B38%5D=Rhode%20Island&state%5B39%5D=South%20Carolina&state%5B40%5D=South%20Dakota&state%5B41%5D=Tennessee&state%5B42%5D=Texas&state%5B43%5D=Utah&state%5B44%5D=Vermont&state%5B45%5D=Virginia&state%5B46%5D=Washington&state%5B47%5D=West%20Virginia&state%5B48%5D=Wisconsin&state%5B49%5D=Wyoming'

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
}

empty_field = ''
result_csv = 'data/brokers.csv'


def get_number_page(url):
    # total number of pages

    src = requests.get(url=url, headers=headers).text
    soup = BeautifulSoup(src, 'lxml')
    number = int(soup.find_all(class_='page-item')[-2].text)
    return number


def get_all_pages(url, total_pages):
    # collect url pages

    for i in range(1, total_pages + 1):
        current_url = f'{url}&page={i}'
        get_items_links(url=current_url)
        print(f'***Proceeded page {i} from {total_pages} - OK')


def get_items_links(url):
    # collect urls to brokers.txt

    src = requests.get(url=url, headers=headers).text
    soup = BeautifulSoup(src, 'lxml')
    target = soup.find_all('div', class_='grid-cell p-2')
    for e in target:
        if 'Company:' not in e.text:
            broker = (e.find_next('a', href=True))
            broker_url = f"https://brokers.interexo.com/{broker['href']}"
            with open('data/brokers.txt', 'a', encoding='utf-8') as f:
                f.write(f'{broker_url}\n')


def adress_split(broker_address_1, broker_address_2):
    # split broker address as separate elements

    city = empty_field
    state = empty_field
    street_number = empty_field
    street_name = empty_field

    if broker_address_1:
        data_1 = [s for s in broker_address_1.split(', ')][1:]
        state = data_1[0]
        if len(data_1) > 1:
            city = data_1[1]

    if broker_address_2:
        data_2 = [s for s in broker_address_2.split()]
        street_number = data_2[0]
        street_name = ' '.join(data_2[1:])

    return street_number, street_name, city, state


def write_data_csv(data):
    with open(result_csv, 'a', encoding='utf-8', newline='') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(data)


def collect_data(url):
    # get brokers information from target url

    src = requests.get(url=url, headers=headers).text
    soup = BeautifulSoup(src, 'lxml')
    broker_name = soup.find('h1', class_='company-name').text.strip()
    broker_about = ' '.join(soup.find('div', class_='row pt-4 company-description').text.strip().split())
    brokerage_name = soup.find('div', class_='col-auto').find('b').text.strip()

    pt1 = soup.find_all('div', class_='pt-1')  # address-1, phone
    pt3 = soup.find_all('div', class_='pt-3')  # address-2, email, site

    broker_address_2 = empty_field
    broker_email = empty_field
    broker_website = empty_field

    for i in range(len(pt3)):
        elem = pt3[i].text.strip()
        if len(elem) > 0:
            if '@' in elem:
                broker_email = elem
            elif 'http' in elem:
                broker_website = elem
            else:
                broker_address_2 = ' '.join(elem.strip().split())

    broker_address_1 = pt1[0].text.strip()

    broker_phone = []
    broker_phones = pt1[1:]
    for phone in broker_phones:
        broker_phone.append(phone.text.strip())

    street_number, street_name, city, state = adress_split(broker_address_1, broker_address_2)

    return (broker_name, broker_about, brokerage_name, street_number, street_name, city, state,
            broker_email, ", ".join(broker_phone), broker_website)


def main():

    if not os.path.exists('data/brokers.txt'):
        total_page = get_number_page(url)
        get_all_pages(url, total_page)

    # write csv headers row
    headers_row = ["Broker's Name", "About", "Brokerage", "Street Number", "Street Name", "City", "State",
                   "Email", "Phone", "Website"]
    if not os.path.exists(result_csv):
        with open(result_csv, 'a', encoding='utf-8', newline='') as csvf:
            writer = csv.writer(csvf)
            writer.writerow(headers_row)

    total_brokers_number = len(re.findall(r"[\n']+", open('data/brokers.txt', encoding='utf-8').read()))

    count = 0
    with open('data/brokers.txt', encoding='utf-8') as f:
        for line in f:
            data = collect_data(url=line.strip())
            write_data_csv(data)
            count += 1
            print(f'*** Proceeded url {count} from {total_brokers_number} - OK')
            print(*data, sep='\n')  # control output in console
            print(20 * '=')
            # if count == 5:
            #     break


if __name__ == '__main__':
    main()
