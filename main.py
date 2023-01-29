import os
import pycurl
import certifi
from io import BytesIO
import urllib.parse
from bs4 import BeautifulSoup

buffer = BytesIO()
c = pycurl.Curl()

LAST_PERIOD = 10

html = ""
if os.path.exists("test.html1"):
    with open("test.html", "r") as f:
        html = f.read()
else:
    URL = "https://talos.stuy.edu/auth/login/"

    print("""Please enter your Talos login information. 
    This information is not saved or sent anywhere other than talos.stuy.edu.
    This script is open source and can be found at """)
    USERNAME = input("E-mail: ")
    PASSWORD = input("Password: ")
    CSRF = ""

    # get the CSRF token
    c.setopt(c.URL, URL)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.COOKIEJAR, 'cookie.txt')
    c.setopt(c.CAINFO, certifi.where())
    # c.setopt(c.VERBOSE, True)
    c.perform()

    html = buffer.getvalue().decode('iso-8859-1')
    soup = BeautifulSoup(html, 'html.parser')
    # print(soup.prettify())
    CSRF = soup.find('input').attrs["value"]

    # get the html page containing schedule

    post_data = {
        'csrfmiddlewaretoken': CSRF,
        'login': USERNAME,
        'password': PASSWORD,
    }
    postfields = urllib.parse.urlencode(post_data)

    c.setopt(c.URL, URL)

    c.setopt(c.POST, True)
    c.setopt(c.POSTFIELDS, postfields)
    c.setopt(c.COOKIEJAR, 'cookie.txt')
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.CAINFO, certifi.where())
    # c.setopt(c.VERBOSE, True)
    c.perform()

    # Ending the session and freeing the resources
    c.close()

    if os.path.exists("cookie.txt"):
        os.remove("cookie.txt")
    else:
        print("The file does not exist")

    html = buffer.getvalue().decode('iso-8859-1')


# extract the schedule
fields = ["Period", "Course ID", "Course Name",
          "Section", "Cycle", "Teacher", "Room"]
schedule = []

soup = BeautifulSoup(html, 'html.parser')
table_body = soup.find_all("tbody")[-1]
table_rows = table_body.find_all("tr")

# convert to python list of lists
for row in table_rows:
    cols = row.find_all("td")
    cols = [e.text.strip() for e in cols]
    schedule.append(cols)

# deal with double periods
for row in schedule:
    if int(row[0]) > LAST_PERIOD:
        for i in range(2):
            new_row = row.copy()
            new_row[fields.index("Period")
                    ] = new_row[fields.index("Period")][i]
            new_row[fields.index("Cycle")] = new_row[fields.index("Cycle")].split()[
                i]
            schedule.insert(int(new_row[fields.index("Period")])-1, new_row)
for row in schedule:
    if int(row[0]) > LAST_PERIOD:
        schedule.remove(row)

# add free periods
for i in range(1, LAST_PERIOD+1):
    if i not in [int(row[0]) for row in schedule]:
        schedule.insert(i-1, [f'{i}', "N/A", "FREE",
                        "0", "MTWRF", "ARISTOTLE", "NO ROOM"])

# change Cycle to be a list
for row in schedule:
    row[fields.index("Cycle")] = "\"[" + ", ".join(
        [i for i in list(row[fields.index("Cycle")]) if i != "-"]) + "]\""

# export to csv
with open("schedule.csv", "w") as f:
    f.write(",".join(fields))
    for row in schedule:
        f.write("\n")
        for e in row:
            f.write(f"{e}, ")

print(fields)
for row in schedule:
    print(row)
