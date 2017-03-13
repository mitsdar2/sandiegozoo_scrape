import json
import sys
import requests
import bs4 # beautiful soup 4
import datetime
import dryscrape # to mimic wget with javascript behavior

ROOT = 'http://animals.sandiegozoo.org'
ERROR_LOG_FILENAME = 'error.log'

def log_error(text):
    with open(ERROR_LOG_FILENAME,'w+') as f:
        f.write('{}: {}\n'.format(datetime.datetime.now().time(), text))

# Return a requests object of the HTML page requested
def get_page(url):
    response = requests.get(url, verify=False)
    return response


def get_root_page():
    # Download root page html
    root_name = ''
    with open("root.txt", 'r') as f:
        root_name = f.read()

    response = get_page(root_name)

    with open("root_page.html","w") as f:
        f.write(response.text)

def load_root_html():
    # Open and read all html in root page
    text = ''
    with open("animals",'r') as f:
        text = f.read()
    
    return text

# Parse the text and return a list of dictionaries of function names and URLs
def get_child_pages(text):
    soup = bs4.BeautifulSoup(text, 'html.parser')

    # extract the huge table of funcs
    #table = soup.find('table', attrs={'class': 'index-fn'})
    animal_spans = soup.find_all('span') #, attrs={'field-content'})

    data = []
    # Add the url dictionary for each animal
    for span in animal_spans:
        try:
            if(ROOT in span.a['href']):
                continue
            #print(span.a['href'])
            data.append( {'url' : prepend_root_url(span.a['href']),'done' : False } )
        except:
            pass

    return data 


def prepend_root_url(text):
    return "{}{}".format(ROOT,text)


def https_to_http(url):
    ret = url
    return ret.replace("https","http")

def write_animal_data(data):
    with open("animal_info.txt","w") as f:
        #print(data)
        for entry in data:
            #print(entry)
            f.write("URL: {}\n".format(entry['url']))

    with open("animal_info.jl","w") as f:
        for entry in data:
            f.write("{}\n".format(json.dumps(entry)))

def append_animal_text(dict_):
    try:
        with open("animal_final.txt","a") as f:        
            f.write(dict_['name'])
            f.write(dict_['classification'])
            f.write(dict_['about'])
            f.write(dict_['habitat_diet'])
            f.write(dict_['conservation'])
            f.write(dict_['sidebar'])
    except Exception as e:
        log_error(e)


if __name__ == "__main__":
    #get_root_page() # don't need to call this anymore
    text = load_root_html() # load root html file from disk
    data = get_child_pages(text) # parse html to get list of dictionaries of func names and urls
    write_animal_data(data)

    done = 0
    total = len(data)

    print("There are {} pages.".format(total))

    for dict_ in data:
        if dict_['done'] is True:
            continue

        url = dict_['url']
        #url = https_to_http(url)

        tmp = (done*1.0/total)*100
        print("Accessing {}".format(url))
        print("{}% complete...".format(tmp))
        session = dryscrape.Session()
        session.visit(url)
        response = session.body()
        soup = bs4.BeautifulSoup(response, 'html.parser')

        animal_name = soup.find_all(True, {'class': 'field field-node--node-title field-name-node-title field-type-ds field-label-hidden'})

        for an in animal_name:
            dict_['name'] = an.text.encode('utf8')
            #print(an.text.encode('utf8'))

        classification = soup.find_all(True, {'class': 'clearfix text-formatted field field-node--field-classifications field-name-field-classifications field-type-text-long field-label-hidden'})

        # there should only be one!
        for c in classification:
            dict_['classification'] = c.text.encode('utf8')
            #print(c.text.encode('utf8'))
            #print('--- end classification ---')

        about = soup.find_all(True, {'class' : 'paragraph paragraph--type--paragraph-green paragraph--view-mode--default'})

        for a in about:
            dict_['about'] = a.text.encode('utf8')
            #print(a.text.encode('utf8'))
            #print('--- end about ---')

        habitat_diet = soup.find_all(True, {'class' : 'paragraph paragraph--type--paragraph-orange paragraph--view-mode--default'})

        for hd in habitat_diet:
            dict_['habitat_diet'] = hd.text.encode('utf8')
            #print(hd.text.encode('utf8'))
            #print('--- end habitat-diet ---')

        conservation = soup.find_all(True, {'class' : 'paragraph paragraph--type--paragraph-yellow paragraph--view-mode--default'})

        for c in conservation:
            dict_['conservation'] = c.text.encode('utf8')
            #print(c.text.encode('utf8'))
            #print('--- end conservation ---')

        sidebar = soup.find_all(True, {'class' : 'paragraph paragraph--type--sidebar-text paragraph--view-mode--default'})
        temp = ''
        for s in sidebar:
            temp += s.text.encode('utf8')
            #print(s.text.encode('utf8'))
            #print('-- end sidebar ---')

        dict_['sidebar'] = temp

        append_animal_text(dict_)
        done += 1
        print("Done with #{}: {}...".format(done, dict_['name']))
        dict_['done'] = True
        write_animal_data(data) # Update done data
