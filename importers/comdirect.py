from beancount.ingest.importer import ImporterProtocol
import warnings
from datetime import datetime, date, timedelta
from pathlib import Path
import re

class NoNewBalanceException(Exception):
    """
    Raised in case the CSV file does not have a new balance.
    """

class InvalidFormatError(Exception):
    """
    Raised in case the CSV file format isn't as expected.
    """

class NoValidEndDateError(Exception):
    """
    Raised in case the CSV file format isn't as expected.
    """

class ComdirectImporter(ImporterProtocol):
    def __init__(self, account, iban, currency='EUR'):
        self.account = account
        self.iban = iban
        self.currency = currency
        self.date_start = None
        self.date_end = None

        super().__init__()

    def identify(self, file):
        with open(file.name, encoding="ISO-8859-1") as fd:
            line = fd.readline().strip()
            line2 = fd.readline().strip()
            print(line)
            print(line2)        
            return line == ';' and  line2.startswith("\"Umsätze Girokonto\";") 
        
    
    def extract(self, file):
        if not self.identify(file):
            warnings.warn(f'{file.name} is not compatible with ComdirectImporter')
            return []
        
        line_index = -1
        with open(file.name, encoding="ISO-8859-1") as fd:
            line = fd.readline().strip()
            line_index += 1
            
            
            # metadata: end date
            line = fd.readline().strip()
            line_index += 1
            
            
            self.date_start = self.extract_start_date(line, file.name)
            self.date_end = self.extract_end_date(line, file.name)

            # metadate: new balance
            line_index += 1
            line = fd.readline().strip()
           

            if not line.startswith('"Neuer kontostand";'):
                raise NoNewBalanceException('File does not have a new balance')                
                
    
            balance_amount = None
            balance_line_index = None




    def file_account(self, file):
        return self.account
    

    def extract_dates(self, line, filename):
        try:
            
             # Extracting the date and timestamp of file upon creation by filename
            path = Path(filename)
            filename = path.name                      
            _, _,date_str = filename.split('_')
            date_str, time_str = date_str.split('-')
            time_str, _ = time_str.split('.')
        
            _, value, _ = line.split(';')
            value = value.strip('"')
            date_pattern = r'\b\d{2}\.\d{2}\.\d{4}\b'
            dates = re.findall(date_pattern, line)
            print(dates)
            
            if len(dates) == 2:
                # two strings. Extract start and end date of transactions in this file
                date_format = "%d.%m.%Y"
                date_objects = [datetime.strptime(date_str, date_format).date() for date_str in dates]                
                return (date_objects[0], date_objects[1])            
                
            elif value.startswith("Zeitraum:"):
                # the end date is a timestamp that is coded into the filename
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:])     
                end_date = datetime(year, month, day)
                
                # The start date is x days before end date
                match = re.search(r'(\d+)\s*Tage', value)
                delta = 0
                if match:
                    delta = int(match.group(1))  # Extract the number and convert it to an integer                    
                else:
                    print("No match found")
                    raise InvalidFormatError(f'Invalid metadata: {line}')

                d = timedelta(days = delta) 
                start_date = end_date - d

                return (start_date, end_date)

            return None
        except ValueError:
            raise InvalidFormatError(f'Invalid metadata: {line}')
        
        
