from beancount.ingest.importer import ImporterProtocol
from beancount.core.amount import Amount
from decimal import Decimal
import warnings
from datetime import datetime, date, timedelta
from pathlib import Path
import re
import csv
from beancount.core import data
import os.path

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



def parse_date(date_str):
    if date_str.lower() == "offen":
        return None  # You can return None or any other placeholder for unknown dates
    try:
        # Parse the date in the expected format "dd.mm.yyyy"
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        # Handle cases where the format is unexpected or invalid
        return None

class ComdirectImporter(ImporterProtocol):
    def __init__(self, account, iban, account_nr, currency='EUR'):
        self.account_nr = account_nr
        self.account = account
        self.iban = iban
        self.currency = currency
        self.date_start = None
        self.date_end = None

        super().__init__()

    def file_account(self, file):
        return self.account

    def file_date(self, file):
        return super().file_date(file)

    def file_date(self, file):
        self.extract(file)
        return self.date_end
    
    def file_name(self, file):
        _, extension = os.path.splitext(os.path.basename(file.name))
        return f'comdirect{extension}'

    def identify(self, file):
        """
        Identify if the given file is compatible with the ComdirectImporter.

        Args:
            file: A file-like object to be checked.

        Returns:
            bool: True if the file is compatible, False otherwise.
        """
        if self.account_nr not in file.name:
            return False

        with open(file.name, encoding="ISO-8859-1") as fd:
            line = fd.readline().strip()
            line2 = fd.readline().strip()                 
            return line == ';' and line2.startswith("\"Umsätze Girokonto\";") 
        
    

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
            
            
            (self.date_start, self.date_end) = self.extract_dates(line, file.name)
            
            # metadate: new balance            
            line = fd.readline().strip()
            line_index += 1

            if not line.startswith('"Neuer Kontostand";'):
                raise NoNewBalanceException('File does not have a new balance')                
                
            balance, currency = self.extract_balance(line)
            balance_amount = Amount(Decimal(balance), currency)
            balance_line_index = line_index


            # parse transactions

            line = fd.readline().strip()
            line_index += 1

            if line:
                raise InvalidFormatError(
                'Empty line expected after header is not empty'
                )
            # data entries
            reader = csv.DictReader(fd, delimiter=';', quoting=csv.QUOTE_MINIMAL, quotechar='"')
            line_index +=1
            entries = []


            for row in reader:
                line_index += 1
               
                # Todo: This way of getting the balance at the beginning of the period is ugly
                # The data got caught up in the dictionary and the labels dont make sense
                # maybe I have to pass two times through the file. One time reading all 
                # metadata and the second time to use only part of the file for the dict
                # containing all the transactions
                if row['Buchungstag'] == 'Alter Kontostand':
                    old_balance_str = row['Wertstellung (Valuta)']
                    old_balance_str = old_balance_str.replace('.', '')
                    old_balance_str = old_balance_str.replace(',', '.')
                    amount_str, currency = old_balance_str.split(' ')
                    old_balance = Amount(Decimal(amount_str), currency)                    
                    break

                meta = data.new_metadata(file.name, line_index)
                amount_str = row['Umsatz in EUR'].replace('.', '') # remove the '1000 dots'
                amount_str = amount_str.replace(',', '.') # decimal comma to decimal point.
                amount = Amount(Decimal(amount_str), self.currency)
                
                date_str = row['Buchungstag'] 
                parsed_date = parse_date(date_str)

                if parsed_date is None:
                    continue
                else:                    
                    date = parsed_date

                description = row['Buchungstext']
                postings = [
                    data.Posting(
                        self.account, amount, None, None, None, None
                    )
                ]
                entries.append(
                    data.Transaction(
                        meta,
                        date,
                        self.FLAG,
                        None,
                        description,
                        data.EMPTY_SET,
                        data.EMPTY_SET,
                        postings,
                    )
                )
                line_index += 1


            # Add balance on end date
            meta = data.new_metadata(fd.name, balance_line_index)

            """From the book Tracking Personal Finances using Python: The difference is subtle but extremely important. Essentially, the CSV tells us that the balance of our
            account at the end of dd.mm.yyyy was x EUR. Beancount, on the other hand, expects dates to
            correspond to the beginning of the day. To account for this difference, we add a timedelta of 1 day
            to date_end when instantiating data.Balance so that the balances will add up."""
            entries.append(
                data.Balance(
                    meta,
                    self.date_end + timedelta(days=1),
                    self.account,
                    balance_amount,
                    None,
                    None,
                )
            )

            return entries



    
    def file_account(self, file):
        return self.account
    

    def extract_dates(self, line, filename):
        try:
            # Extract date and time from the filename
            end_date = self._extract_date_from_filename(filename)

            # Extract dates from the line
            dates = self._extract_dates_from_line(line)

            if len(dates) == 2:
                return dates[0], dates[1]
            elif "Zeitraum:" in line:
                start_date = self._calculate_start_date(line, end_date)
                return start_date, end_date
            else:
                raise InvalidFormatError(f'Invalid metadata: start and end dates could not be determined. {line}')
        except ValueError:
            raise InvalidFormatError(f'Invalid metadata: {line}')

    def _extract_date_from_filename(self, filename):
        path = Path(filename)
        filename = path.name
        _, _, date_str = filename.split('_')
        date_str, _ = date_str.split('-')
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:])
        return datetime(year, month, day).date()

    def _extract_dates_from_line(self, line):
        date_pattern = r'\b\d{2}\.\d{2}\.\d{4}\b'
        date_strings = re.findall(date_pattern, line)
        date_format = "%d.%m.%Y"
        return [datetime.strptime(date_str, date_format).date() for date_str in date_strings]

    def _calculate_start_date(self, line, end_date):
        match = re.search(r'(\d+)\s*Tage', line)
        if match:
            delta_days = int(match.group(1))
            return end_date - timedelta(days=delta_days)
        else:
            raise InvalidFormatError(f'Invalid metadata: start date could not be determined. {line}')
        
        
    def extract_balance(self, line):
        #"Neuer Kontostand";"4.588,30 EUR";
        _, balance, _ = line.split(';')
        amount_str, currency = balance.split(' ')
        currency = currency.replace('"','')
        converted_number = amount_str.replace('.', '').replace(',', '.').replace('"','')

        amount = Decimal(converted_number) # maybe don convert to float as it is later put into a Decimal.
        return amount, currency



