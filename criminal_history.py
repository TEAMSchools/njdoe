from . import BeautifulSoup, requests

SESSION = requests.Session()

class ApprovalRecord:
    def __init__(self, applicant, approval_history):
        self.applicant = applicant.__dict__
        self.approval_history = approval_history.records

class Applicant:
    def __init__(self, applicant_tr):
        applicant_p_list = applicant_tr.find_all('p')
        for p in applicant_p_list:
            p_split = p.text.split(':')
            p_key = p_split[0].replace(' ', '_').lower()
            p_value = p_split[1].strip()

            setattr(self, p_key, p_value)

class ApprovalHistory:
    def __init__(self, approval_tr_list):
        self.records = []

        for tr in approval_tr_list:
            td_list = tr.find_all('td')

            approval_record = {}
            for td in td_list:
                td_key = td.attrs['class'][0]
                approval_record[td_key] = td.text.strip()

            self.records.append(approval_record)

def applicant_approval_employment_history(ssn1, ssn2, ssn3, dob_month, dob_day, dob_year):
    payload = {
        'ssn1': ssn1,
        'ssn2': ssn2,
        'ssn3': ssn3,
        'dobmonth': dob_month,
        'dobday': dob_day,
        'dobyear': dob_year,
        'version': 'html',
    }

    results_page = SESSION.post('https://homeroom5.doe.state.nj.us/chrs18/?app-emp-history', data=payload)

    results_html = results_page.text
    results_soup = BeautifulSoup(results_html, 'lxml')
    results_tables = results_soup.find_all('table', {'class' : r'apprv-list'}) # results table

    if results_tables:
        applicant_tr = results_tables[0].find('tr', attrs={'class': 'applicant'}) # applicant data, pull only from 1st table
        applicant_record = Applicant(applicant_tr)

        approval_tr_lists = []
        for rt in results_tables:
            approval_tr_list = [tr for tr in rt.find_all('tr') if tr.find_all('td')] # approval data
            approval_tr_lists.extend(approval_tr_list)

        approval_history = ApprovalHistory(approval_tr_lists)

        applicant_approval_record = ApprovalRecord(applicant_record, approval_history)

        return applicant_approval_record.__dict__

    else:
        return {}