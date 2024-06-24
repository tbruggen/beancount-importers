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
            
            
            self.date_start, self.date_end = self.extract_end_date(line, file.name)

            # metadate: new balance
            line_index += 1
            line = fd.readline().strip()
           

            if not line.startswith('"Neuer kontostand";'):
                raise NoNewBalanceException('File does not have a new balance')                
                
    
            balance_amount = None
            balance_line_index = None




    def file_account(self, file):
        return self.account

    def extract_end_date(self, line, filename):
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
                #date_string = "01.06.2024"
                date_format = "%d.%m.%Y"
                date_objects = [datetime.strptime(date_str, date_format).date() for date_str in dates]
                
                is_date_or_datetime = lambda x: isinstance(x, (date, datetime))
                
                return all(is_date_or_datetime(d) for d in dates)
            
                
            elif value.startswith("Zeitraum:"):
                # the end date is a timestamp that is coded into the name of the csv file
                

               
                
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:])                
                hour = int(time_str[:2])
                minute = int(time_str[2:])
                date_object = datetime(year, month, day, hour, minute)
                
                return date_object

            return None
        except ValueError:
            raise InvalidFormatError(f'Invalid metadata: {line}')
        
        
