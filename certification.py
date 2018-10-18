from . import BeautifulSoup, requests
import re

BASE_URL = 'https://www20.state.nj.us/DOE_TCIS_ASC'
SESSION = requests.Session()

class CertificationRecord:
    def __init__(self, applicant, application_history, certificate_history):
        self.applicant = applicant.data
        self.application_history = application_history.records

        if certificate_history is None:
            self.certificate_history = []
        else:
            self.certificate_history = certificate_history.records

class Applicant:
    def __init__(self, certificates_applicant_table):
        self.data = {}

        applicant_td_list = certificates_applicant_table.find_all('td')

        applicant_td_list_grouped = zip(*(iter(applicant_td_list),) * 2)
        for i, td in enumerate(applicant_td_list_grouped):
            td0 = td[0].text.lower().strip()
            if td0 == '':
                pass
            else:
                td0 = td0.replace(' ', '_')
                td0 = td0.replace(':', '')
                td1 = td[1].text.strip()
                self.data[td0] = td1

class CertificateHistory:
    def __init__(self, certificates_history_table):
        self.records = []

        certificates_headers_list = certificates_history_table.find_all('td', attrs={'class': 'whiteHdrs'})
        certificates_headers_list_clean = []
        for h in certificates_headers_list:
            h_text = h.text
            h_text = h_text.replace('#', 'number')
            h_text = h_text.replace('(MM/YYYY)', '')
            h_text = h_text.replace('/', '_')
            h_text = h_text.strip().lower()
            h_text = h_text.replace(' ', '_')
            h_text = h_text.replace('\xa0', '_')
            certificates_headers_list_clean.append(h_text)

        certificates_tr_list = certificates_history_table.find_all('tr', attrs={'class': ['darkBG', 'lightBG']})
        for tr in certificates_tr_list:
            record = {}
            certificates_td_list = tr.find_all('td')
            for i, td in enumerate(certificates_td_list):
                record[certificates_headers_list_clean[i]] = td.text.strip()

            self.records.append(record)

class ApplicationHistory:
    def __init__(self, application_history_table):
        self.records = []

        applications_headers_list = application_history_table.find_all('td', attrs={'class': 'whiteHdrs'}) # table headers

        applications_headers_list_clean = []
        applications_headers_list_clean.append('index')
        for h in applications_headers_list:
            h_text = h.text
            h_text = h_text.strip().lower()
            h_text = h_text.replace(' ', '_')
            applications_headers_list_clean.append(h_text)

        applications_tr_list = application_history_table.find_all('tr', attrs={'class': ['darkBG', 'lightBG']}) # table data

        applications_data_list = []
        rowspan_data = []
        for i, tr in enumerate(applications_tr_list):
            applications_td_list = tr.find_all('td')

            record_data = []
            for j, td in enumerate(applications_td_list):
                ## save rowspan value and positional data
                if td.attrs.get('rowspan'):
                    rowspan_data.append((i, j, int(td.attrs['rowspan']), td.text.strip()))
                record_data.append(td.text.strip())

            for j, td in enumerate(applications_td_list):
                td_a = td.find('a')
                if td_a:
                    a_href = td_a.attrs['href']
                    re_match = re.search('\d+', a_href)
                    td_index = re_match[0]
                    record_data.insert(0, td_index)

                    ## save rowspan value and positional data
                    if td.attrs.get('rowspan'):
                        rowspan_data.append((i, 0, int(td.attrs['rowspan']), td_index))

                    break

            applications_data_list.append(record_data)

        ## backfill rowspan data
        if rowspan_data:
            for rd in rowspan_data:
                for k in range(1, rd[2]):
                    applications_data_list[rd[0] + k].insert(rd[1], rd[3])

        ## create dicts from app data list
        applications_data = []
        for ad in applications_data_list:
            application_record = {}
            for l, d in enumerate(ad):
                application_record[applications_headers_list_clean[l]] = d

            applications_data.append(application_record)

        for a in applications_data:
            application_record = Application(**a)

            self.records.append(application_record.__dict__)

class Application:
    def __init__(self, index, application_number, date_received, endorsement, certificate_type, request_type, status):
        self.index = index
        self.application_number = application_number
        self.date_received = date_received
        self.endorsement = endorsement
        self.certificate_type = certificate_type
        self.request_type = request_type
        self.status = status
        self.index = index

        self.checklist = self._certificate_checklist()

    def _certificate_checklist(self):
        checklist_params = {'appSeq': int(self.index)}
        checklist_page = SESSION.get(f'{BASE_URL}/pages/intakeCheckList.jsp', params=checklist_params)
        checklist_text = checklist_page.text
        checklist_soup = BeautifulSoup(checklist_text, 'lxml')
        checklist_tables = checklist_soup.find_all('table')

        checklist = ApplicationChecklist(checklist_tables)

        return checklist.__dict__

class ApplicationChecklist:
    def __init__(self, checklist_tables):
        filing_date_table = checklist_tables[1]
        checklist_table = checklist_tables[2]

        self.filing_date = self._filing_date(filing_date_table)
        self.tasks = self._certificate_checklist_items(checklist_table)

    def _filing_date(self, filing_date_table):
        filing_date_td = filing_date_table.find('td', attrs={'class': 'blueRegularText'}) # data is in td with this class
        filing_date_center = filing_date_td.find('center')
        filing_date = filing_date_center.find(text=True).strip()
        return filing_date

    def _certificate_checklist_items(self, checklist_table):
        checklist_tr_list = checklist_table.find_all('tr', attrs={'class': ['darkBG', 'lightBG']}) # checklist table data

        tasks = []
        for tr in checklist_tr_list:
            td_list = tr.find_all('td')

            checkbox_img = td_list[0].find('img')
            task_complete = 'checkbox.png' in checkbox_img.attrs['src']
            task_name = td_list[1].text.strip()
            task_comment = td_list[2].text.strip()

            task = ApplicationChecklistItem(task_name, task_comment, task_complete)
            tasks.append(task.__dict__)

        return tasks

class ApplicationChecklistItem:
    def __init__(self, task, comment, complete):
        self.task = task
        self.comment = comment
        self.complete = complete

def application_status_check(last_name, ssn1, ssn2, ssn3):
    SESSION.get(f'{BASE_URL}/pages/appStatusSearch.jsp')

    search_payload = {
        'action': '',
        'lastname': last_name,
        'ssn1': ssn1,
        'ssn2': ssn2,
        'ssn3': ssn3,
    }

    results_page = SESSION.post(f'{BASE_URL}/appStatusSearch.do', data=search_payload)
    results_html = results_page.text
    results_soup = BeautifulSoup(results_html, 'lxml')

    tracking_number_td = results_soup.find('td', attrs={'class': 'instructionTxt'})
    if tracking_number_td:
        tracking_number = tracking_number_td.contents[-1].text

        results_tables = results_soup.find_all('table')
        application_history_table = results_tables[3] # applications table
        application_history = ApplicationHistory(application_history_table)

        ## issued certificates
        certificates_params = {
            'action': 'getCertificationsList',
            'trackingNumber': tracking_number
        }
        certificates_page = SESSION.get(f'{BASE_URL}/appStatusSearch.do', params=certificates_params)
        certificates_page_html = certificates_page.text

        certificates_page_soup = BeautifulSoup(certificates_page_html, 'lxml')
        certificates_page_tables = certificates_page_soup.find_all('table')

        certificates_applicant_table = certificates_page_tables[4]
        applicant = Applicant(certificates_applicant_table)

        if len(certificates_page_tables) >= 9:
            certificates_history_table = certificates_page_tables[8]
            certificate_history = CertificateHistory(certificates_history_table)
        else:
            certificate_history = None

        certificate_record = CertificationRecord(applicant, application_history, certificate_history)

        return certificate_record.__dict__

    else:
        return {}
